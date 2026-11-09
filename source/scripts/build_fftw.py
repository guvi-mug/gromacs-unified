#!/usr/bin/env python3
"""Build static, single-precision FFTW on Windows or Linux for GROMACS."""
import argparse
from pathlib import Path
import shutil
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--work', type=Path, default=Path('.native/fftw-build'))
    parser.add_argument('--jobs', type=int, default=2)
    args = parser.parse_args()
    source, output, work = args.source.resolve(), args.output.resolve(), args.work.resolve()
    subprocess.run(['cmake', '-S', str(source), '-B', str(work),
                    '-DCMAKE_POLICY_VERSION_MINIMUM=3.5', '-DCMAKE_BUILD_TYPE=Release',
                    f'-DCMAKE_INSTALL_PREFIX={output}', '-DBUILD_SHARED_LIBS=OFF',
                    '-DENABLE_FLOAT=ON', '-DENABLE_SSE=ON', '-DENABLE_SSE2=ON',
                    '-DDISABLE_FORTRAN=ON', '-DBUILD_TESTS=ON'], check=True)
    subprocess.run(['cmake', '--build', str(work), '--config', 'Release',
                    '--parallel', str(args.jobs)], check=True)
    # FFTW 3.3.10 registers CTest cases only when Threads_FOUND. Run its
    # verification executable explicitly for static non-threaded builds too.
    candidates = [work / 'bench', work / 'bench.exe', work / 'Release/bench.exe']
    bench = next(path for path in candidates if path.is_file())
    for problem in ('32x64', 'ib256'):
        subprocess.run([str(bench), '--verify', problem], check=True)
    subprocess.run(['cmake', '--install', str(work), '--config', 'Release'], check=True)
    licenses = output / 'licenses'
    licenses.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source / 'COPYING', licenses / 'FFTW-COPYING')


if __name__ == '__main__':
    main()
