#!/usr/bin/env python3
"""Keep upstream physical tests and thresholds, selecting only device/threads."""
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('engine_source', type=Path)
parser.add_argument('--backend', choices=('cpu', 'cuda'), required=True)
parser.add_argument('--threads', type=int, default=4)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
source = args.engine_source / 'tests/physicalvalidation/systems.json'
systems = json.loads(source.read_text())
placement = '-nb cpu -pme cpu -bonded cpu -update cpu' if args.backend == 'cpu' else '-nb gpu'
for system in systems:
    system['mdrun_args'] = f'-ntmpi 1 -ntomp {args.threads} {placement}'
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(systems, indent=2) + '\n')
print(f'Prepared {len(systems)} unchanged upstream physical-validation systems')
