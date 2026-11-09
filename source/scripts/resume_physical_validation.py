#!/usr/bin/env python3
"""Resume prepared upstream trajectories without overwriting completed runs."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--work', type=Path, required=True)
parser.add_argument('--gmx', type=Path, required=True)
parser.add_argument('--engine-source', type=Path, required=True)
parser.add_argument('--backend', choices=('cpu', 'cuda'), required=True)
parser.add_argument('--threads', type=int, default=4)
args = parser.parse_args()
gmx = args.gmx.resolve()
env = os.environ.copy()
env['PATH'] = str(gmx.parent) + os.pathsep + env.get('PATH', '')
if os.name != 'nt':
    env['LD_LIBRARY_PATH'] = str(gmx.parent.parent / 'lib') + os.pathsep + env.get('LD_LIBRARY_PATH', '')
env['MPLBACKEND'] = 'Agg'
env['GMX_NO_QUOTES'] = '1'
inputs = sorted(args.work.resolve().rglob('system.mdp'))
if len(inputs) != 46:
    raise RuntimeError(f'Expected 46 prepared subruns, found {len(inputs)}')
for number, mdp in enumerate(inputs, 1):
    directory = mdp.parent
    target = int(re.search(r'^\s*nsteps\s*=\s*(\d+)', mdp.read_text(), re.M | re.I).group(1))
    log = directory / 'system.log'
    text = log.read_text(encoding='utf-8', errors='replace') if log.exists() else ''
    steps = re.findall(r'Step\s+Time\s*\n\s*(\d+)', text)
    if steps and int(steps[-1]) >= target and 'Finished mdrun' in text:
        print(f'[{number}/46] already complete: {directory}', flush=True)
        continue
    with (directory / 'resume-console.txt').open('a', encoding='utf-8') as stream:
        if not (directory / 'system.tpr').exists():
            subprocess.run([str(gmx), 'grompp', '-f', 'system.mdp', '-p', 'system.top',
                            '-c', 'system.gro', '-o', 'system.tpr'], cwd=directory,
                           env=env, stdout=stream, stderr=subprocess.STDOUT, check=True)
        command = [str(gmx), 'mdrun', '-s', 'system.tpr', '-deffnm', 'system',
                   '-ntmpi', '1', '-ntomp', str(args.threads)]
        command += ['-nb', 'gpu'] if args.backend == 'cuda' else [
            '-nb', 'cpu', '-pme', 'cpu', '-bonded', 'cpu', '-update', 'cpu']
        if (directory / 'system.cpt').exists():
            command += ['-cpi', 'system.cpt']
        print(f'[{number}/46] running/resuming: {directory}', flush=True)
        subprocess.run(command, cwd=directory, env=env, stdout=stream,
                       stderr=subprocess.STDOUT, check=True)
source = args.engine_source.resolve() / 'tests/physicalvalidation'
subprocess.run([sys.executable, str(source / 'gmx_physicalvalidation.py'),
                str(source / 'systems.json'), '--gmx', str(gmx),
                '--wd', str(args.work.resolve()), '-a'], env=env, check=True)
