# Reproduce extended validation

The normal unit and smoke tests are described in [INSTALLATION.md](INSTALLATION.md).
These additional checks use the official regression suite, upstream physical
validation, and public MPI-NAT benchmark systems. Use separate output directories
for every OS/backend so simulations do not overwrite one another.

## External regression suite

```bash
python source/scripts/fetch_sources.py regressiontests --destination .native/sources
```

The exact 2026.4 archive is SHA-256 pinned. It also matched the MD5 recorded in
the upstream 2026.4 release source. Put the desired engine's `bin` directory on
PATH, create an empty working directory, and run from it:

```bash
perl /absolute/path/to/regressiontests-2026.4/gmxtest.pl all -nosuffix -nt 2 -ntomp 2 -noverbose
```

On Linux set `LD_LIBRARY_PATH` to that engine's `lib` directory. On Windows use
**native Windows Perl**, such as Strawberry Perl, rather than the MSYS Perl
distributed with Git. MSYS Perl treats CRLF output differently and produced
false text-reference failures here. No regression thresholds were relaxed.
The native CPU engines each passed 42 complex cases and 7 essential-dynamics
cases; CUDA engines each passed 88 complex variants plus 7 essential-dynamics
cases. The suite contains no extra cases in this release (`All 0 extra`).

## Physical validation

The upstream driver and bundled `physical_validation` library are in
`tests/physicalvalidation` under the extracted GROMACS engine source. Use a
separate uv environment with Python 3.12 and the pinned analysis dependencies:

```bash
uv venv --python 3.12 .venv-validation
uv pip install --python .venv-validation/bin/python -r source/tests/physical-validation-requirements.txt
python source/scripts/prepare_physical_validation.py .native/sources/gromacs-2026.4 --backend cpu --output .native/physical-cpu.json
.venv-validation/bin/python -u .native/sources/gromacs-2026.4/tests/physicalvalidation/gmx_physicalvalidation.py .native/physical-cpu.json --gmx /absolute/path/to/cpu/bin/gmx --wd /absolute/path/to/physical-cpu
```

On Windows replace `bin/python` with `Scripts/python.exe` and use a native
`gmx.exe` path. Use `.venv-validation-wsl` when sharing the Windows checkout
with WSL. For CUDA prepare a separate JSON with `--backend cuda`, select the
CUDA executable, and choose a new working directory. Setting `MPLBACKEND=Agg`
avoids opening plot windows during analysis.

When analyzing configurations concurrently, give every analysis process a
different current working directory as well as a different `--wd`. The upstream
parser uses a fixed temporary XVG filename in its current directory. The resume
helper now selects the configuration's own directory for the analysis subprocess.
Sharing a current directory caused extraction collisions in early parallel
analysis attempts; rerunning in isolated directories cleared those errors.

The JSON retains all upstream systems, trajectory lengths, random seeds, and
statistical thresholds. Only thread count and CPU/GPU placement are selected.
The full single-precision configuration contains 14 systems and 46 simulation
subruns, including integration convergence, ensemble sampling, and kinetic
energy distribution checks. Statistical failures must be reported rather than
removed by changing tolerances.

## Larger production-like simulations

```bash
python source/scripts/fetch_benchmarks.py
python source/scripts/benchmark_runtime.py --inputs .native/benchmarks --output .native/benchmarks-runs/local-cpu --backend cpu
python source/scripts/benchmark_runtime.py --inputs .native/benchmarks --output .native/benchmarks-runs/local-cuda --backend cuda
```

The downloader verifies SHA-256 pins for both inputs. Defaults run `benchMEM`
for 50,000 steps (100 ps) and `benchRIB` for 2,000 steps (8 ps), using four
threads and one thread-MPI rank. The script checks native completion and finite
final potential energy and temperature, preserves logs, and records a JSON
summary. These systems suppress frequent energy output, so this is a longer
stability/workload check rather than a high-resolution energy-drift study.

The 82k-atom membrane protein and 2M-atom solvated ribosome are research-derived
benchmarks from the [Max Planck benchmark collection](https://www.mpinat.mpg.de/grubmueller/bench).
They use legacy all-bond constraints, so GPU runs still perform coordinate
updates on CPU. These runs do not validate an arbitrary future production
system or long-timescale scientific conclusions. Throughput measured while
other validation jobs run is labeled as shared-load throughput.

Input attribution (CC-BY 4.0): Department of Theoretical and Computational
Biophysics, Max Planck Institute for Multidisciplinary Sciences, Göttingen.

See [the local validation report](validation-logs/native-validation-2026-11-08.md)
for the observed results and remaining limits.
