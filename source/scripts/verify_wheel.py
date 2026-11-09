#!/usr/bin/env python3
"""Install a platform wheel into a clean venv and run the bundled engine."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile
import venv


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dist', type=Path)
    parser.add_argument('--interface-only', action='store_true', help='validate Python-only wheel without engines')
    args = parser.parse_args()
    wheels = list(args.dist.glob('*.whl'))
    if len(wheels) != 1:
        parser.error('Expected exactly one wheel in output directory')
    repo = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix='gmx wheel ') as directory:
        venv.EnvBuilder(with_pip=True).create(directory)
        python = Path(directory) / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
        env = {key: value for key, value in os.environ.items()
               if key not in ('PYTHONPATH', 'GMX_RUNTIME_ROOT', 'GMX_CPU_EXECUTABLE', 'GMX_CUDA_EXECUTABLE')}
        subprocess.run([str(python), '-m', 'pip', 'install', '--no-deps', str(wheels[0].resolve())],
                       check=True, env=env)
        subprocess.run([str(python), '-m', 'gromacs_unified', 'doctor'], check=True, env=env)
        if args.interface_only:
            subprocess.run([str(python), '-m', 'unittest', 'discover', '-s', str(repo / 'tests'), '-v'],
                           check=True, env=env, cwd=directory)
        else:
            subprocess.run([str(python), str(repo / 'scripts/smoke_test.py'), '--backend', 'cpu'],
                           check=True, env=env, cwd=directory)


if __name__ == '__main__':
    main()
