# Restart handoff â€” 8 November 2026

> **Current status, 8 November 2026 at 22:02 CST:** all eight large benchmark runs completed. Windows CUDA physical validation passed all 14 systems after completing 46/46 trajectories. The other three physical suites are active. Do not launch duplicate resume commands while their job states are `running`.

NVIDIA driver 621.14 passed Windows and WSL CUDA smoke tests after the reboot. Durable job states are in `.native/validation-jobs/*.state.json`, with output in `validation-logs/resumed-*.log`. Preserve `.native/`, the uv virtual environments, and `/home/gavi/gromacs-unified-build` in WSL.

## Completed validation

- Windows CPU and CUDA: all 86 upstream CTest suites per engine.
- WSL CPU and CUDA: all 94 upstream CTest suites per engine.
- External regression: CPU engines each passed 42 complex + 7 essential-dynamics cases; CUDA engines each passed 88 complex variants + 7 essential-dynamics cases.
- Python interface/helpers: 26 tests pass on each OS; GitHub CI passes.
- Python/CLI smoke matrix passed CPU, CUDA, auto GPU, and hidden-GPU CPU fallback.
- All four configurations completed both MPI-NAT benchmarks: membrane 50,000 steps / 100 ps; ribosome 2,000 steps / 8 ps. Energies and temperatures are finite and logs contain no detected constraint/runtime failures.
- Windows CUDA physical validation: all 46 trajectories and all 14 systems passed.

A separate comparison exposed a large-system mixed-precision CPU absolute-energy limitation, independently of the wrapper. See [the investigation](validation-logs/ribosome-energy-investigation.md). The release remains a prerelease; benchmark execution is not a cross-backend accuracy pass.

## Physical-validation snapshot

| Configuration | Completed trajectories | Final analysis |
| --- | --- | --- |
| Windows CPU | 37 / 46 | Pending |
| Windows CUDA | 46 / 46 | All 14 systems passed |
| WSL CPU | 39 / 46 | Pending |
| WSL CUDA | 34 / 46 | Pending |

Counts are a timestamped snapshot, not a live display. Integrator checks and all five argon systems passed on all four configurations. Further water systems passed individually, but a partial analysis is not a full suite pass. Original trajectory lengths and thresholds are unchanged.

The benchmark continuation helper was corrected to pass only missing steps: GROMACS interprets `-nsteps` relative to the checkpoint. Three helper tests cover this; the physical continuation uses no step override. Parallel analysis now uses a distinct current directory per configuration because the upstream parser uses a fixed temporary XVG filename.

## Resume Windows

From `C:\Users\Yoshi\projects\gromacs-unified`:

```powershell
. ./Activate-Gromacs.ps1
python source/scripts/benchmark_runtime.py --inputs .native/benchmarks --output .native/benchmarks-runs/windows-cpu --backend cpu --resume
.venv-validation/Scripts/python.exe -u source/scripts/resume_physical_validation.py --work .native/physical/windows-cpu --gmx .native/windows/runtime/cpu/bin/gmx.exe --engine-source .native/sources/gromacs-2026.4 --backend cpu
.venv-validation/Scripts/python.exe -u source/scripts/resume_physical_validation.py --work .native/physical/windows-cuda --gmx .native/windows/runtime/cuda/bin/gmx.exe --engine-source .native/sources/gromacs-2026.4 --backend cuda
```

The physical resume helper skips completed trajectories, continues checkpoints,
and starts unstarted trajectories. It retains original lengths and thresholds,
then invokes the unchanged upstream analysis. Resume-helper syntax was checked;
the resumed runs are active after the requested stop. Check job state before starting any duplicate command.

## Resume WSL

In Ubuntu, from `/mnt/c/Users/Yoshi/projects/gromacs-unified`:

```bash
source ./activate-gromacs-wsl.sh
python source/scripts/benchmark_runtime.py --inputs .native/benchmarks --output /home/gavi/gromacs-unified-build/benchmarks-linux-cpu --backend cpu --resume
.venv-validation-wsl/bin/python -u source/scripts/resume_physical_validation.py --work /home/gavi/gromacs-unified-build/physical-cpu --gmx .native/linux/runtime/cpu/bin/gmx --engine-source .native/sources/gromacs-2026.4 --backend cpu
.venv-validation-wsl/bin/python -u source/scripts/resume_physical_validation.py --work /home/gavi/gromacs-unified-build/physical-cuda --gmx .native/linux/runtime/cuda/bin/gmx --engine-source .native/sources/gromacs-2026.4 --backend cuda
```

These are long jobs. Current settings use four threads per run. Preserve their
console output with shell redirection if running unattended. Completed GPU
benchmarks do not need repeating.

## Release and repository

- Code: https://github.com/guvi-mug/gromacs-unified
- Prebuilds: https://github.com/guvi-mug/gromacs-unified/releases/tag/v0.2.0
- Exact asset hashes: `prebuilds/v0.2.0/SHA256SUMS`
- Local wheels: `wheels/windows-built/` and `wheels/linux-built/`
- Local logs: `validation-logs/` (generated `.log` files are excluded from Git)

Release users should follow `INSTALLATION.md`. Linux assets require glibc 2.43+
and GLIBCXX 3.4.32+; GPU assets target SM 120. The CPU engine is also bundled.
