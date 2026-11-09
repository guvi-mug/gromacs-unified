#!/usr/bin/env python3
"""Download pinned upstream sources, verify hashes, and extract safely."""
import argparse
import hashlib
from pathlib import Path
import tarfile
import urllib.request

SOURCES = {
    'gromacs': ('2026.4', 'https://ftp.gromacs.org/gromacs/gromacs-2026.4.tar.gz',
                '58eda60979b124fcf9dff8b1b63cedfbc72fdb36d99e921dc1bdc310571098b6'),
    'fftw': ('3.3.10', 'https://www.fftw.org/fftw-3.3.10.tar.gz',
             '56c932549852cddcfafdab3820b0200c7742675be92179e59e6215b340e26467'),
    'regressiontests': ('2026.4', 'https://ftp.gromacs.org/regressiontests/regressiontests-2026.4.tar.gz',
                        'c1d9b1f8518100fdf113d32f3a67e5d5934bb456cf2e0ba8cb4bceba748ded8f'),
}


def fetch(name, destination):
    version, url, expected = SOURCES[name]
    destination.mkdir(parents=True, exist_ok=True)
    archive = destination / url.rsplit('/', 1)[-1]
    if not archive.exists():
        temporary = archive.with_suffix('.part')
        try:
            with urllib.request.urlopen(url, timeout=120) as source, temporary.open('wb') as target:
                while chunk := source.read(1024 * 1024):
                    target.write(chunk)
            temporary.replace(archive)
        finally:
            temporary.unlink(missing_ok=True)
    actual = hashlib.sha256(archive.read_bytes()).hexdigest()
    if actual != expected:
        raise ValueError(f'Checksum mismatch for {archive.name}: {actual}; remove archive and retry')
    output = destination / f'{name}-{version}'
    if output.exists():
        raise FileExistsError(f'{output} already exists; use a fresh source directory')
    with tarfile.open(archive) as source:
        # Validate traversal first, then let the data filter verify link targets.
        for member in source.getmembers():
            resolved = (destination / member.name).resolve()
            if not resolved.is_relative_to(destination.resolve()):
                raise ValueError('Unsafe archive member')
            if not (member.isfile() or member.isdir() or member.issym() or member.islnk()):
                raise ValueError('Archive special files are not supported')
        if not hasattr(tarfile, 'data_filter'):
            raise RuntimeError('Source extraction requires Python with tarfile.data_filter (Python 3.12+)')
        source.extractall(destination, filter='data')
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('name', choices=SOURCES)
    parser.add_argument('--destination', type=Path, default=Path('.native/sources'))
    args = parser.parse_args()
    print(fetch(args.name, args.destination))
