#!/usr/bin/env python3
"""Download hash-pinned MPI-NAT benchmarks used for extended validation."""
import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import zipfile

INPUTS = {
    'benchMEM': '3c1c8cd4f274d532f48c4668e1490d389486850d6b3b258dfad4581aa11380a4',
    'benchRIB': '39acb014a79ed9a9ff2ad6294a2c09f9b85ea6986dfc204a3639814503eeb60a',
}

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--destination', type=Path, default=Path('.native/benchmarks'))
args = parser.parse_args()
args.destination.mkdir(parents=True, exist_ok=True)
for name, expected in INPUTS.items():
    archive = args.destination / (name + '.zip')
    if not archive.exists():
        temporary = archive.with_suffix('.part')
        try:
            subprocess.run(['curl.exe' if os.name == 'nt' else 'curl', '--fail', '--location',
                            '--silent', '--show-error', 'https://www.mpinat.mpg.de/' + name,
                            '--output', str(temporary)], check=True)
            temporary.replace(archive)
        finally:
            temporary.unlink(missing_ok=True)
    actual = hashlib.sha256(archive.read_bytes()).hexdigest()
    if actual != expected:
        raise ValueError(f'Checksum mismatch for {archive}: {actual}')
    output = (args.destination / name).resolve()
    if not output.exists():
        with zipfile.ZipFile(archive) as bundle:
            for member in bundle.infolist():
                if not (output / member.filename).resolve().is_relative_to(output):
                    raise ValueError('Unsafe benchmark archive member')
            bundle.extractall(output)
    print(f'Verified {name}: {actual}')

# CC-BY 4.0 attribution for the downloaded input files:
# Department of Theoretical and Computational Biophysics, Max Planck Institute
# for Multidisciplinary Sciences, Göttingen, https://www.mpinat.mpg.de/grubmueller/bench
