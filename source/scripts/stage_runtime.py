#!/usr/bin/env python3
"""Stage native installations into a platform wheel's package data."""
import argparse
import json
from pathlib import Path
import platform
import shutil
import tempfile


def stage(source, destination, allow_unchecked=False):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if source == destination or source.is_relative_to(destination) or destination.is_relative_to(source):
        raise ValueError('Source and package runtime directories must be separate')
    if destination.exists():
        raise FileExistsError(f'{destination} exists; remove the old generated runtime first')
    backends = [backend for backend in ('cpu', 'cuda') if (source / backend).is_dir()]
    if 'cpu' not in backends:
        raise ValueError('An independent CPU engine is required for a distributable bundle')
    name = 'gmx.exe' if platform.system() == 'Windows' else 'gmx'
    for backend in backends:
        prefix = source / backend
        if not (prefix / 'bin' / name).is_file():
            raise ValueError(f'Missing native executable for {backend}')
        info = json.loads((prefix / 'build-info.json').read_text(encoding='utf-8'))
        if info['system'] != platform.system() or info['machine'].lower() != platform.machine().lower():
            raise ValueError('Build platform differs from packaging platform')
        if info['backend'] != backend:
            raise ValueError('Backend manifest mismatch')
        if not allow_unchecked and not info.get('checks_passed'):
            raise ValueError('Upstream checks were skipped; use --allow-unchecked only for development')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as temporary:
        staged = Path(temporary) / 'runtime'
        for backend in backends:
            shutil.copytree(source / backend, staged / backend)
        staged.rename(destination)
    return destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--destination', type=Path, default=Path('src/gromacs_unified/runtime'))
    parser.add_argument('--allow-unchecked', action='store_true')
    args = parser.parse_args()
    print(stage(args.source, args.destination, args.allow_unchecked))
