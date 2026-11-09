"""Keep real Python/CLI simulation artifacts for CPU, CUDA, auto and fallback."""
import argparse
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
from gromacs_unified import Gromacs

parser = argparse.ArgumentParser()
parser.add_argument('--runtime-root', help='omit to validate package-bundled discovery')
parser.add_argument('--output', required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
output = Path(args.output).resolve()
output.mkdir(parents=True, exist_ok=True)
runtime_root = str(Path(args.runtime_root).resolve()) if args.runtime_root else None
engine = Gromacs(runtime_root=runtime_root)
results = []
for label, backend, hidden in [('cpu', 'cpu', False), ('cuda', 'cuda', False), ('auto', 'auto', False), ('auto-no-gpu', 'auto', True)]:
    work = output / label
    work.mkdir(exist_ok=False)
    for item in (root / 'tests/fixtures/argon').iterdir():
        shutil.copy2(item, work / item.name)
    env = {'CUDA_VISIBLE_DEVICES': '-1'} if hidden else {}
    result = engine.run('grompp', '-f', 'md.mdp', '-c', 'conf.gro', '-p', 'topol.top', '-o', 'run.tpr', backend='cpu', cwd=work, capture_output=True)
    (work / 'grompp-output.txt').write_text(result.stdout + result.stderr, encoding="utf-8")
    result = engine.mdrun('-s', 'run.tpr', '-deffnm', 'python', '-ntmpi', 1, '-ntomp', 1, backend=backend, cwd=work, capture_output=True, env=env)
    (work / 'python-output.txt').write_text(result.stdout + result.stderr, encoding="utf-8")
    cli = [sys.executable, '-m', 'gromacs_unified']
    if runtime_root:
        cli += ['--runtime-root', runtime_root]
    cli += ['--backend', backend, 'mdrun', '-s', 'run.tpr', '-deffnm', 'cli', '-ntmpi', '1', '-ntomp', '1']
    result = subprocess.run(cli, cwd=work, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True, env={**os.environ, **env})
    (work / 'cli-output.txt').write_text(result.stdout + result.stderr, encoding="utf-8")
    energies = []
    for name in ('python', 'cli'):
        engine.run('energy', '-f', name + '.edr', '-o', name + '.xvg', input='Potential\n0\n', backend='cpu', cwd=work, capture_output=True)
        values = [float(line.split()[1]) for line in (work / (name + '.xvg')).read_text(encoding="utf-8", errors="replace").splitlines() if line.strip() and not line.startswith(('#', '@'))]
        assert len(values) == 21 and all(math.isfinite(v) for v in values)
        energies.append(values)
    assert all(math.isclose(a, b, rel_tol=1e-5, abs_tol=1e-5) for a, b in zip(*energies))
    gpu_used = 'GPU selected for this run' in (work / 'python.log').read_text(encoding="utf-8", errors="replace")
    assert gpu_used == (label in ('cuda', 'auto')), f'Unexpected device selection for {label}'
    row = {'mode': label, 'gpu_used': gpu_used, 'samples': len(energies[0]), 'final_potential': energies[0][-1], 'python_cli_match': True}
    results.append(row)
    print(json.dumps(row), flush=True)
(output / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
