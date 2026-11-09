# Restart handoff — 8 November 2026

> **Resumed:** the six unfinished jobs were restarted after the reboot, with
> NVIDIA driver 621.14. Both Windows and WSL CUDA smoke tests passed. Background
> job states are in `.native/validation-jobs/*.state.json`, with output in
> `validation-logs/resumed-*.log`. Do not launch duplicate resume commands while
> these jobs are running. Both CPU benchmark jobs have since completed. The stopped-state counts below are historical.
>
> The benchmark resume helper was corrected to pass only the missing steps:
> GROMACS interprets `-nsteps` relative to the checkpoint. A checkpoint at
> step 43,920 now runs 6,080 further steps to reach 50,000. Physical-validation
> resumes do not use this override and were unaffected. Three regression tests
> were added; all 26 interface/helper tests pass.

All active simulation processes were stopped for the requested computer restart.
Windows received console stop signals; Linux received SIGTERM. Existing outputs
and checkpoint files are preserved. Do not delete `.native/`, the virtual
environments, or `/home/gavi/gromacs-unified-build` in WSL.

## Completed validation

- Windows CPU and CUDA: all 86 upstream suites passed for each engine.
- WSL CPU and CUDA: all 94 upstream suites passed for each engine.
- External regression: CPU engines each passed 42 complex + 7 essential-dynamics
  cases; CUDA engines each passed 88 complex variants + 7 essential-dynamics cases.
- Python interface: 26 tests passed on each OS; GitHub CI also passed all four jobs.
- Python/CLI smoke matrix passed CPU, CUDA, auto GPU, and hidden-GPU CPU fallback.
- Both CUDA engines finished the membrane benchmark (50,000 steps, 100 ps)
  and ribosome benchmark (2,000 steps, 8 ps), with finite energies/temperatures.
- Both CPU engines have now completed both benchmark systems as well. All eight
  large runs reached their requested final steps with finite energies/temperatures.
- A CPU/CUDA difference in initial ribosome potential energy is being investigated;
  successful execution alone does not establish cross-backend accuracy.

## Physical validation remains incomplete

| Configuration | Fully completed simulation subruns |
| --- | --- |
| Windows CPU | 24 / 46 |
| Windows CUDA | 24 / 46 |
| WSL CPU | 31 / 46 |
| WSL CUDA | 19 / 46 |

These are trajectory counts, not final suite pass counts. Preliminary integrator
checks on Windows CPU and WSL CUDA passed, as did the first analyzed Linux CPU
ensemble and Maxwell–Boltzmann checks. Full final statistical analysis is pending.
The GitHub binaries are marked **prerelease** for this incomplete validation.

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
