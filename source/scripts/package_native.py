#!/usr/bin/env python3
"""Package checked CPU/CUDA engines together without altering the source tree."""
import argparse
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile

from stage_runtime import stage


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('runtime', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--uv', default='uv')
    parser.add_argument('--install', action='store_true')
    args = parser.parse_args()
    source = Path(__file__).resolve().parents[1]
    output = args.out.resolve()
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='gromacs package ') as temporary:
        package = Path(temporary) / 'source'
        shutil.copytree(source, package, ignore=shutil.ignore_patterns(
            'runtime', '__pycache__', '*.egg-info', '.native', '.venv', 'build', 'dist', '.git'))
        stage(args.runtime, package / 'src/gromacs_unified/runtime')
        if platform.system() == 'Linux':
            from collect_linux_runtime import collect
            collect(package / 'src/gromacs_unified/runtime')
        subprocess.run([args.uv, 'build', '--wheel', str(package), '--out-dir', str(output)], check=True)
    wheels = list(output.glob('gromacs_unified-*.whl'))
    if len(wheels) != 1:
        raise RuntimeError('Expected one platform wheel; use a separate output directory per platform')
    print(wheels[0], flush=True)
    if args.install:
        subprocess.run([args.uv, 'pip', 'install', '--python', sys.executable,
                        '--reinstall', str(wheels[0])], check=True)


if __name__ == '__main__':
    main()
