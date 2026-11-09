#!/usr/bin/env python3
"""Build identical runtime layouts with CMake on Linux and Windows."""
import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys


def collect_windows_runtime(executable):
    subprocess.run([
        'cmake', f'-DEXECUTABLE={executable}',
        f'-DOUTPUT_DIRECTORY={executable.parent}',
        '-P', str(Path(__file__).with_name('collect_windows_runtime.cmake').resolve())
    ], check=True)


def commands(source, output, work, backend, args):
    build, prefix = work / backend, output / backend
    configure = ['cmake', '-S', str(source), '-B', str(build),
                 f'-DPython3_EXECUTABLE={sys.executable}',
                 '-DCMAKE_BUILD_TYPE=Release', f'-DCMAKE_INSTALL_PREFIX={prefix}',
                 f'-DGMX_GPU={"CUDA" if backend == "cuda" else "OFF"}',
                 '-DGMX_MPI=OFF', '-DGMX_THREAD_MPI=ON', '-DGMX_DOUBLE=OFF',
                 '-DGMX_DEFAULT_SUFFIX=OFF', '-DGMX_BINARY_SUFFIX=',
                 '-DBUILD_SHARED_LIBS=OFF', '-DGMX_BUILD_SHARED_EXE=OFF',
                 '-DGMXAPI=OFF', f'-DGMX_SIMD={args.simd}',
                 '-DREGRESSIONTEST_DOWNLOAD=OFF', '-DGMX_BUILD_UNITTESTS=ON']
    if args.generator:
        configure += ['-G', args.generator]
    if args.fftw_prefix:
        configure += ['-DGMX_FFT_LIBRARY=fftw3', '-DGMX_BUILD_OWN_FFTW=OFF',
                      f'-DCMAKE_PREFIX_PATH={Path(args.fftw_prefix).resolve()}']
    elif args.fft == 'fftpack':
        configure += ['-DGMX_FFT_LIBRARY=fftpack', '-DGMX_BUILD_OWN_FFTW=OFF']
    elif os.name == 'nt':
        raise ValueError('Windows requires --fftw-prefix; --fft fftpack is for smoke tests')
    else:
        if 'Ninja' in (args.generator or os.environ.get('CMAKE_GENERATOR', '')):
            raise ValueError('Own-FFTW requires Makefiles; supply --fftw-prefix for Ninja')
        configure += ['-DGMX_FFT_LIBRARY=fftw3', '-DGMX_BUILD_OWN_FFTW=ON']
    configure.extend(args.cmake_arg)
    common = ['--config', 'Release', '--parallel', str(args.jobs)]
    result = [configure, ['cmake', '--build', str(build), *common]]
    if not args.skip_checks:
        result.append(['cmake', '--build', str(build), '--target', 'check', *common])
    result.append(['cmake', '--install', str(build), '--config', 'Release'])
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path, help='runtime root containing cpu/ and cuda/')
    parser.add_argument('--backend', choices=('cpu', 'cuda', 'both'), default='both')
    parser.add_argument('--work', type=Path, default=Path('.native/build'))
    parser.add_argument('--jobs', type=int, default=2)
    parser.add_argument('--simd', default='SSE2', help='portable x86-64; override for ARM')
    parser.add_argument('--fft', choices=('fftw3', 'fftpack'), default='fftw3')
    parser.add_argument('--fftw-prefix')
    parser.add_argument('--generator')
    parser.add_argument('--skip-checks', action='store_true', help='development only')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--cmake-arg', action='append', default=[])
    args = parser.parse_args(argv)
    if args.jobs < 1:
        parser.error('--jobs must be positive')
    source, output, work = args.source.resolve(), args.output.resolve(), args.work.resolve()
    if not (source / 'src/gromacs/CMakeLists.txt').is_file():
        parser.error('source must be an extracted upstream GROMACS engine release')
    backends = ('cpu', 'cuda') if args.backend == 'both' else (args.backend,)
    try:
        plans = [(backend, commands(source, output, work, backend, args)) for backend in backends]
    except ValueError as error:
        parser.error(str(error))
    if args.dry_run:
        print(json.dumps([cmd for _, plan in plans for cmd in plan], indent=2))
        return 0
    if 'cuda' in backends and not shutil.which('nvcc'):
        parser.error('CUDA toolkit nvcc required; use --backend cpu on CPU build hosts')
    for backend, plan in plans:
        manifest = output / backend / 'build-info.json'
        manifest.unlink(missing_ok=True)
        for command in plan:
            if os.name == 'nt' and '--target' in command and 'check' in command:
                # Upstream tests load CUDA DLLs before installation. Newer CUDA
                # toolkits keep them in bin/x64, which may not be on PATH.
                bindir = work / backend / 'bin'
                executable = next(path for path in (
                    bindir / 'gmx.exe', bindir / 'Release/gmx.exe'
                ) if path.is_file())
                collect_windows_runtime(executable)
            print(subprocess.list2cmdline(command), flush=True)
            subprocess.run(command, check=True)
        if os.name == 'nt':
            collect_windows_runtime(output / backend / 'bin/gmx.exe')
        license_dir = output / backend / 'licenses'
        license_dir.mkdir(parents=True, exist_ok=True)
        for name in ('COPYING', 'AUTHORS', 'README'):
            if (source / name).is_file():
                shutil.copy2(source / name, license_dir / name)
        if args.fftw_prefix:
            third_party = Path(args.fftw_prefix) / 'licenses'
            if third_party.is_dir():
                shutil.copytree(third_party, license_dir / 'fftw', dirs_exist_ok=True)
        for path in (source / 'src/external').rglob('*'):
            if path.is_file() and path.name.upper().startswith(('LICENSE', 'COPYING')):
                target = license_dir / 'external' / path.relative_to(source / 'src/external')
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
        if backend == 'cuda' and os.environ.get('CUDA_PATH'):
            eula = Path(os.environ['CUDA_PATH']) / 'EULA.txt'
            if eula.is_file():
                shutil.copy2(eula, license_dir / 'CUDA-EULA.txt')
        manifest.write_text(json.dumps({
            'backend': backend, 'system': platform.system(), 'machine': platform.machine(),
            'checks_passed': not args.skip_checks, 'configure': plan[0],
            'source': str(source), 'fft': 'fftw3' if args.fftw_prefix else args.fft,
        }, indent=2) + '\n', encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
