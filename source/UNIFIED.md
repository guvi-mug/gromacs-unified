# GROMACS Unified

One Python package and command-line interface for native Windows and Linux
GROMACS, with automatic selection, explicit CPU/CUDA modes, and bundled native
engines. The shared API launches native GROMACS; the numerical engine remains
upstream GROMACS. This is a working development project, not a published release.

## Install and use

Install a platform wheel from a native build to get the Python library, CLI,
and engine data together:

```bash
python -m pip install /path/to/gromacs_unified-0.2.0-py3-none-PLATFORM.whl
```

Or install the Python interface from this checkout and use existing engines:

```bash
python -m pip install .
gmx-unified doctor
gmx-unified --backend auto mdrun -s topol.tpr -deffnm run
gmx-unified --backend cpu mdrun -s topol.tpr -deffnm run_cpu
gmx-unified --backend cuda mdrun -s topol.tpr -deffnm run_gpu
gmx-unified grompp -f md.mdp -c conf.gro -p topol.top -o topol.tpr
```

The commands work in a Windows developer/user shell and on Linux. Use
`python -m gromacs_unified` if the console script directory is absent from PATH.
Launcher options precede the native tool name; native options follow it.
`--dry-run` prints the selected argv without starting a simulation.

| Mode | Behavior on either OS |
| --- | --- |
| auto | Prefer a loadable CUDA engine; let GROMACS detect usable devices and place work. Use the CPU engine if the CUDA engine cannot load. |
| cpu | Prefer the independent CPU engine. Force nonbonded, PME, FFT, bonded, and update work to CPU. A loadable CUDA engine can also run CPU mode. |
| cuda | Require a CUDA engine and GPU nonbonded work. Missing/incompatible visible GPUs produce a native GROMACS error. Other tasks use automatic placement. |

A CUDA build still performs some work on CPU. CUDA mode does not mean every
simulation operation runs on the GPU. GPU visibility and simulation compatibility
are checked by GROMACS itself, rather than inferred from `nvidia-smi`. `doctor`
reports engine loadability and compiled support, not a usable GPU count.
Switch modes between invocations; use normal `-cpi` options to resume compatible
checkpoints. No simulation is silently retried after a failure.

## Python API

```python
from gromacs_unified import Gromacs

gmx = Gromacs()  # discovers a bundled engine automatically
print(gmx.doctor())
gmx.mdrun("-s", "topol.tpr", "-deffnm", "run", backend="auto")
gmx.mdrun("-s", "topol.tpr", "-deffnm", "run_cpu", backend="cpu")
result = gmx.run("energy", "-f", "run.edr", "-o", "energy.xvg",
                 input="Potential\n0\n", capture_output=True)
print(result.stdout)
```

The same code works with Windows `gmx.exe` and Linux `gmx`. `run()` returns
`subprocess.CompletedProcess` and raises `CalledProcessError` on failure by
default. It supports `cwd`, `input`, `capture_output`, `check`, `timeout`, and
per-child environment overrides such as `env={"CUDA_VISIBLE_DEVICES": "0"}`.
Native streams are inherited by default. String, numeric and path arguments are
passed directly without a shell. Custom offload placement and external MPI
launchers currently use native GROMACS directly. This wrapper is separate from
the upstream gmxapi workflow library.

## Engine discovery

For each backend, discovery uses this order:

1. `Gromacs(cpu=..., cuda=...)`, CLI executable arguments, or
   `GMX_CPU_EXECUTABLE` / `GMX_CUDA_EXECUTABLE`.
2. `Gromacs(runtime_root=...)`, CLI `--runtime-root`, or `GMX_RUNTIME_ROOT`.
3. Package-local `gromacs_unified/runtime`.
4. `gmx` on PATH.

Each runtime root contains `cpu/bin/gmx[.exe]`, `cuda/bin/gmx[.exe]`, and intact
installation trees including force fields. CUDA is optional; a standalone CPU
engine is required in bundles so machines without a CUDA runtime can still run.
DLL/library search paths are scoped to child processes. Explicit invalid CPU
paths fail CPU mode rather than silently substituting another installation.

## Build requirements

Build tools use Python 3.12+, CMake 3.28+, and a supported C++ compiler. On Linux
use GCC 13 and Make/Ninja. On Windows use the x64 Visual Studio 2022 developer
shell; the native build does not require WSL. The hosted workflow selects
the installed v142 toolset through Ninja to match CUDA 12.6. CUDA additionally requires a
supported toolkit and host-compiler pair (the workflow uses CUDA 12.6.3).
A compatible NVIDIA driver is required on GPU execution hosts. Windows users
also need the supported Microsoft Visual C++ runtime.

The default SIMD target is SSE2 for x86-64 portability. Set `--simd AVX2_256`
only when all target CPUs support it. ARM builds need an appropriate SIMD option;
they are outside the current CI matrix.

## Reproducible source and native builds

The download helper pins SHA-256 hashes for upstream GROMACS 2026.4 and FFTW
3.3.10. It verifies archives before extracting them; existing extracted trees
must be removed or a new destination used for a fresh download.

Run these commands on either build OS (PowerShell accepts these one-line forms):

```bash
python -m pip install "cmake>=3.28,<4" build wheel
python scripts/fetch_sources.py gromacs
python scripts/fetch_sources.py fftw
python scripts/build_fftw.py .native/sources/fftw-3.3.10 .native/fftw
python scripts/build_native.py .native/sources/gromacs-2026.4 .native/runtime --backend both --fftw-prefix .native/fftw --jobs 2
```

Use `--backend cpu` on build hosts without CUDA. `build_windows.ps1` and
`build_linux.sh` are convenience entry points. Windows FFTW is built separately;
GROMACS's own-FFTW download option does not support Windows. `--fft fftpack`
selects the slower internal library for development smoke tests. `--skip-checks`
is development-only and recorded in the build manifest.

The builder runs upstream unit checks, installs independent native trees,
collects non-system Windows DLL dependencies, and preserves available third-party
licenses. Windows CUDA DLL collection runs on the build machine with the CUDA
bin directory available; unresolved dependencies fail the build. NVIDIA driver
DLLs remain system-provided. CUDA redistribution and the complete license/source
inventory must be reviewed before public release. Linux wheels use the build
host's platform baseline; they are not claimed to be manylinux wheels.

## Bundle and validate

```bash
python -m pip install .
python -m unittest discover -s tests -v
python scripts/smoke_test.py --runtime-root .native/runtime --backend cpu
python scripts/smoke_test.py --runtime-root .native/runtime --backend auto
python scripts/smoke_test.py --runtime-root .native/runtime --backend cuda
python scripts/stage_runtime.py .native/runtime
python -m build --wheel
python scripts/verify_wheel.py dist
```

Run the CUDA smoke command on a compatible GPU host. Smoke tests prepare an
included two-particle argon simulation, run it through Python and the CLI, and
compare finite potential-energy samples. They verify integration and argument
handling, not broad scientific accuracy or production performance. Wheel
verification installs into a fresh virtual environment and repeats the CPU
simulation using the bundled engine, exercising relocation and engine discovery.
Staging rejects unchecked builds by default; `--allow-unchecked` marks an
explicit development packaging path. Remove old generated package runtime and
dist directories before making a new wheel to avoid stale assets.

The Python CI matrix covers Windows/Linux and Python 3.10/3.12. The manual
`Native engines and wheels` workflow builds native engines and wheels on both
OSes, runs CPU/auto smoke tests, and uploads artifacts without publishing.
Hosted runners provide no CUDA hardware validation; CUDA simulation tests must
also pass on a GPU machine before a CUDA release is called tested. The manual
`GPU hardware validation` workflow targets a self-hosted runner labeled `gpu`
and the chosen OS, using its existing CPU/CUDA runtime directory.

## Project status

Implemented: shared API/CLI, bundled-engine discovery, independent CPU/CUDA
build plans, Windows dependency collection, native source pinning, platform wheel
packaging, unit tests, and real simulation verification tooling.

Native Windows and WSL Linux CPU/CUDA execution was validated locally on
8 November 2026 using an RTX 5080. Windows requires the tracked compatibility
patches for the pinned upstream release. See `VALIDATION.md` for observed
results and the repository-level `INSTALLATION.md` for current build commands.
Local validation does not imply that a GitHub Actions run or release occurred.

References: [GROMACS installation](https://manual.gromacs.org/2026.4/install-guide/index.html),
[runtime placement](https://manual.gromacs.org/2026.4/user-guide/mdrun-performance.html),
[original Windows releases](https://github.com/shoubhikraj/gromacs-windows/releases).
