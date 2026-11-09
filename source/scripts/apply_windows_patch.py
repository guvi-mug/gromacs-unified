#!/usr/bin/env python3
"""Apply the tracked GROMACS 2026.4 Windows fixes exactly once."""
import argparse
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    args = parser.parse_args()
    patch = Path(__file__).resolve().parents[1] / 'patches/windows-2026.4.patch'
    command = ['git', '-C', str(args.source.resolve()), 'apply']
    applied = subprocess.run([*command, '--reverse', '--check', str(patch)],
                             capture_output=True)
    if applied.returncode == 0:
        print('Windows compatibility patch is already applied')
        return
    subprocess.run([*command, '--check', str(patch)], check=True)
    subprocess.run([*command, str(patch)], check=True)
    print('Applied GROMACS 2026.4 Windows compatibility fixes')


if __name__ == '__main__':
    main()
