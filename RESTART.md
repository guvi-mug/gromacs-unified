# Completed validation handoff

As of 2026-11-08 22:57 -0600, all six resumed jobs finished with exit code 0. No validation simulations remain active. Preserve `.native/`, the uv environments, and `/home/gavi/gromacs-unified-build` for raw output and reproduction.

## Final results

- Windows CPU/CUDA: 86 upstream CTest suites passed per engine.
- WSL CPU/CUDA: 94 upstream CTest suites passed per engine.
- External regression: CPU engines each passed 42 complex + 7 essential-dynamics cases; CUDA engines each passed 88 complex variants + 7 essential-dynamics cases.
- Full physical validation: all four configurations completed 46/46 trajectories, all 14 systems and 24 primary checks passed per configuration. No lengths, seeds, or thresholds were reduced.
- Python interface/helpers: all 26 tests pass on both OSes. Python/CLI CPU, CUDA, auto GPU, and hidden-GPU fallback checks passed.
- All eight large MPI-NAT benchmark runs completed: membrane 50,000 steps / 100 ps; ribosome 2,000 steps / 8 ps. Native logs verify exact final steps, finite energies/temperatures, and no detected constraint/runtime failures.

See [physical results](validation-logs/physical-validation-results.json), [benchmark results](validation-logs/benchmark-results.json), and [the validation report](validation-logs/native-validation-2026-11-08.md).

## Remaining accuracy limitation

The release remains a prerelease. The large ribosome input exposed a native mixed-precision CPU absolute-energy limitation, independently of the wrapper. A controlled accumulator correction nearly eliminates the discrepancy in an isolated WSL diagnostic, but that experimental patch is not in the published assets and has not passed the release matrix. See [the investigation](validation-logs/ribosome-energy-investigation.md). Full small-system physical passes do not clear this limitation.

## Continuation details

After the reboot, driver 621.14 passed Windows/WSL CUDA smoke checks. Job states and times are in `.native/validation-jobs/*.state.json`; logs are `validation-logs/resumed-*.log`. The corrected benchmark continuation passes only steps missing after its checkpoint. Analysis uses a distinct current directory per configuration to avoid the upstream parser's temporary-file collision. CMake now receives the invoking uv Python explicitly.

## Optional recheck on Windows

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
all resumed runs have completed. Use these commands only for an intentional recheck.

## Optional recheck on WSL

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
