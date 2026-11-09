#!/usr/bin/env python3
"""Run a real, tiny native simulation through Python and CLI in a temporary dir."""
import argparse
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from gromacs_unified import Gromacs


def smoke(runtime_root=None, backend='cpu'):
    engine = Gromacs(runtime_root=runtime_root)
    fixture = Path(__file__).resolve().parents[1] / 'tests/fixtures/argon'
    with tempfile.TemporaryDirectory(prefix='gromacs smoke ') as temporary:
        work = Path(temporary)
        for item in fixture.iterdir():
            shutil.copy2(item, work / item.name)
        try:
            engine.run('grompp', '-f', 'md.mdp', '-c', 'conf.gro', '-p', 'topol.top',
                       '-o', 'run.tpr', backend='cpu', cwd=work, capture_output=True)
            engine.mdrun('-s', 'run.tpr', '-deffnm', 'python', '-ntmpi', 1, '-ntomp', 1,
                         backend=backend, cwd=work, capture_output=True)
            command = [sys.executable, '-m', 'gromacs_unified', '--backend', backend]
            if runtime_root:
                command += ['--runtime-root', str(Path(runtime_root).resolve())]
            command += ['mdrun', '-s', 'run.tpr', '-deffnm', 'cli', '-ntmpi', '1', '-ntomp', '1']
            subprocess.run(command, cwd=work, capture_output=True, text=True, check=True)
            energies = []
            for name in ('python', 'cli'):
                engine.run('energy', '-f', name + '.edr', '-o', name + '.xvg',
                           input='Potential\n0\n', backend='cpu', cwd=work, capture_output=True)
                values = [float(line.split()[1]) for line in (work / (name + '.xvg')).read_text().splitlines()
                          if line.strip() and not line.startswith(('#', '@'))]
                if not values or not all(math.isfinite(value) for value in values):
                    raise AssertionError('Missing or nonfinite potential energy')
                energies.append(values)
            if len(energies[0]) != len(energies[1]) or any(
                not math.isclose(a, b, rel_tol=1e-5, abs_tol=1e-5)
                for a, b in zip(*energies)
            ):
                raise AssertionError('Python and CLI potential energies differ')
            print(json.dumps({'backend': backend, 'samples': len(energies[0]),
                              'final_potential': energies[0][-1], 'python_cli_match': True}))
        except subprocess.CalledProcessError as error:
            print(error.stdout or '', file=sys.stderr)
            print(error.stderr or '', file=sys.stderr)
            raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-root')
    parser.add_argument('--backend', choices=('cpu', 'auto', 'cuda'), default='cpu')
    args = parser.parse_args()
    smoke(args.runtime_root, args.backend)
