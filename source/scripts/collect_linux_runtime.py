#!/usr/bin/env python3
"""Bundle FFTW/cuFFT runtimes while retaining the host's standard C/C++ ABI."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess


def collect(root):
    for prefix in (Path(root) / 'cpu', Path(root) / 'cuda'):
        executable = prefix / 'bin/gmx'
        if not executable.is_file():
            continue
        libraries = []
        dependencies = subprocess.run(['ldd', str(executable)], capture_output=True,
                                      text=True, check=True).stdout
        if 'not found' in dependencies:
            raise RuntimeError('Unresolved runtime dependency:\n' + dependencies)
        for line in dependencies.splitlines():
            match = re.match(r'\s*(lib(?:fftw3f|cufft)\.so\.[\d.]+) => (\S+)', line)
            if not match:
                continue
            name, original = match.groups()
            source = Path(original).resolve()
            target = prefix / 'lib' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            if source != target.resolve():
                shutil.copy2(source, target)
            libraries.append({'name': name, 'sha256': hashlib.sha256(target.read_bytes()).hexdigest()})
            licenses = prefix / 'licenses'
            licenses.mkdir(exist_ok=True)
            if name.startswith('libfftw'):
                for source_license, output_name in (
                    (Path('/usr/share/doc/libfftw3-single3/copyright'), 'FFTW-system-copyright'),
                    (Path('/usr/share/common-licenses/GPL-2'), 'FFTW-GPL-2'),
                ):
                    if source_license.is_file():
                        shutil.copy2(source_license, licenses / output_name)
            else:
                for directory in source.parents:
                    eula = directory / 'EULA.txt'
                    if eula.is_file():
                        shutil.copy2(eula, licenses / 'CUDA-EULA.txt')
                        break
        abi = {}
        for binary in [executable, *(prefix / 'lib').glob('*.so.*')]:
            versions = subprocess.run(['readelf', '--version-info', str(binary)],
                                      capture_output=True, text=True, check=True).stdout
            for family, version in re.findall(r'\b(GLIBCXX|GLIBC|CXXABI)_([0-9][0-9.]*)', versions):
                parts = tuple(map(int, version.split('.')))
                if family not in abi or parts > tuple(map(int, abi[family].split('.'))):
                    abi[family] = version
        manifest = prefix / 'build-info.json'
        info = json.loads(manifest.read_text())
        info.update(bundled_libraries=libraries, required_system_abi=abi)
        manifest.write_text(json.dumps(info, indent=2) + '\n')
        print(json.dumps({'backend': prefix.name, 'libraries': libraries, 'required_system_abi': abi}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    collect(parser.parse_args().root)
