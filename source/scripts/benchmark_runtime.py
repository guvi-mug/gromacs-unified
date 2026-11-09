#!/usr/bin/env python3
"""Run public, production-like MPI-NAT systems through the installed API."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import time

from gromacs_unified import Gromacs

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--inputs', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--backend', choices=('cpu', 'cuda', 'auto'), required=True)
parser.add_argument('--mem-steps', type=int, default=50000)
parser.add_argument('--rib-steps', type=int, default=2000)
parser.add_argument('--threads', type=int, default=4)
parser.add_argument('--resume', action='store_true')
args = parser.parse_args()
engine = Gromacs()
results = []
for name, steps in [('benchMEM', args.mem_steps), ('benchRIB', args.rib_steps)]:
    tpr = (args.inputs / name / (name + '.tpr')).resolve()
    work = (args.output / name).resolve()
    work.mkdir(parents=True, exist_ok=args.resume)
    start = time.monotonic()
    old_log = work / 'run.log'
    old_text = old_log.read_text(encoding='utf-8', errors='replace') if old_log.exists() else ''
    old_steps = re.findall(r'Step\s+Time\s*\n\s*(\d+)', old_text)
    complete = bool(args.resume and old_steps and int(old_steps[-1]) >= steps and 'Finished mdrun' in old_text)
    with (work / 'console.txt').open('a' if args.resume else 'w', encoding='utf-8') as stream:
        import subprocess
        command = engine.command('mdrun', '-s', tpr, '-deffnm', 'run', '-nsteps', steps,
                                 '-ntmpi', 1, '-ntomp', args.threads, '-pin', 'off',
                                 '-noconfout', backend=args.backend)
        if args.resume and (work / 'run.cpt').exists():
            command += ['-cpi', 'run.cpt']
        if not complete:
            subprocess.run(command, cwd=work, env=engine._environment(command[0]),
                           stdout=stream, stderr=subprocess.STDOUT, check=True)
    elapsed = time.monotonic() - start
    engine.run('energy', '-f', 'run.edr', '-o', 'energies.xvg',
               input='Potential\nTemperature\n0\n', backend='cpu', cwd=work, capture_output=True)
    samples = [list(map(float, line.split())) for line in
               (work / 'energies.xvg').read_text(encoding='utf-8', errors='replace').splitlines()
               if line.strip() and not line.startswith(('#', '@'))]
    if not samples or not all(math.isfinite(v) for row in samples for v in row):
        raise AssertionError('Missing or nonfinite energy/temperature samples')
    log = (work / 'run.log').read_text(encoding='utf-8', errors='replace')
    if 'Finished mdrun' not in log:
        raise AssertionError('Native run did not report completion')
    if re.search(r'LINCS WARNING|SHAKE did not converge|Fatal error|Assertion failed', log):
        raise AssertionError('Native log contains a constraint or runtime failure')
    performance = re.search(r'Performance:\s+([\d.]+)', log)
    row = {'system': name, 'backend': args.backend, 'steps': steps,
           'elapsed_seconds': elapsed, 'energy_samples': len(samples),
           'final_time_ps': samples[-1][0], 'final_potential': samples[-1][1],
           'final_temperature': samples[-1][2],
           'ns_per_day_under_shared_load': float(performance.group(1)) if performance else None,
           'tpr_sha256': hashlib.sha256(tpr.read_bytes()).hexdigest()}
    results.append(row)
    print(json.dumps(row), flush=True)
args.output.joinpath('results.json').write_text(json.dumps(results, indent=2) + '\n')
