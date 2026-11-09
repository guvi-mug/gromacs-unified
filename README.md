# GROMACS Unified

Run GROMACS from one command or from Python on native Windows, WSL2, and Linux.
The launcher supports CPU, NVIDIA CUDA, and automatic device selection.
Automatic mode is the default. See [INSTALLATION.md](INSTALLATION.md) to build
and install the native engines; the Python interface alone does not include them.

## Use a prebuilt package

Download a tested platform wheel and `SHA256SUMS` from
[GitHub Releases](https://github.com/guvi-mug/gromacs-unified/releases/tag/v0.2.0).
These prebuilds are a **prerelease**. A large ribosome input exposed a mixed-precision CPU absolute-energy limitation; see the [measured comparison and reproduction commands](validation-logs/ribosome-energy-investigation.md). Full physical validation passed on all four configurations; the measured large-system CPU energy limitation remains open. See the [validation record](source/VALIDATION.md) for current scope.

Each wheel includes the CLI, Python library, CPU engine, CUDA engine, and
FFTW/cuFFT runtime libraries. You need uv/Python and the platform runtime;
you do not need a compiler, CMake, FFTW installation, or CUDA Toolkit.

| Platform asset | Required setup |
| --- | --- |
| `gromacs_unified-0.2.0-py3-none-win_amd64.whl` | Windows 10/11 x64; current Microsoft Visual C++ v14 x64 Redistributable |
| `gromacs_unified-0.2.0-py3-none-linux_x86_64.whl` | Linux/WSL2 x86-64 with glibc 2.43+, GLIBCXX 3.4.32+, and OpenMP runtime; tested on Ubuntu 26.04 |

GPU mode in these prebuilds targets **SM 120 (RTX 50-series)** and requires a
compatible NVIDIA driver; drivers 592.02 and 621.14 were tested. CPU mode needs no NVIDIA
GPU. Build from source for another GPU architecture or an older Linux runtime.

Install the downloaded wheel into a uv environment:

```powershell
uv venv --python 3.14 .venv
. .\.venv\Scripts\Activate.ps1
uv pip install ./gromacs_unified-0.2.0-py3-none-win_amd64.whl
gmx-unified doctor
```

On Linux/WSL, activate with `source .venv/bin/activate` and install the Linux
wheel instead. No engine paths or environment variables are needed. The
[prebuilt installation section](INSTALLATION.md#install-a-prebuilt-release)
covers prerequisites, checksums, global CLI installation, and smoke tests.

## This Windows workspace

Python is managed by uv in `.venv`. Open a new PowerShell window after the user
PATH change to run `gmx-unified` from any directory. Entering
`~\projects\gromacs-unified` activates its environment at the next prompt.
An existing active environment is preserved. The automatically activated
environment is deactivated when you leave the project.

For immediate manual activation with the local engines:

```powershell
cd ~\projects\gromacs-unified
. .\Activate-Gromacs.ps1
gmx-unified doctor
```

The user PATH entry points to `bin/`, whose launcher uses this project's Python.
The directory activation hook is local setup and must be recreated on another
machine; it is not part of the Python package.

## Command-line use

GROMACS is a command-line application. `gmx-unified` launches its native tools:

```powershell
gmx-unified doctor
gmx-unified grompp -f md.mdp -c conf.gro -p topol.top -o run.tpr
gmx-unified mdrun -s run.tpr -deffnm auto
gmx-unified --backend cpu mdrun -s run.tpr -deffnm cpu
gmx-unified --backend cuda mdrun -s run.tpr -deffnm cuda
gmx-unified energy -f auto.edr -o potential.xvg
gmx-unified mdrun -h
```

Put launcher options such as `--backend` before the GROMACS tool name.
CPU mode forces simulation work to CPU. CUDA mode requires GPU nonbonded work;
other work may remain on CPU. Auto mode lets GROMACS choose available devices
at simulation startup. A CUDA engine and independent CPU engine are bundled
behind the same launcher. `doctor` reports engine availability, not proof that
a simulation can use the GPU. No simulation is retried silently after failure.

## Python library

Run Python from the activated project environment:

```python
from gromacs_unified import Gromacs

gmx = Gromacs()
print(gmx.doctor())
gmx.run("grompp", "-f", "md.mdp", "-c", "conf.gro", "-p", "topol.top",
        "-o", "run.tpr", backend="cpu")
gmx.mdrun("-s", "run.tpr", "-deffnm", "auto", backend="auto")
gmx.mdrun("-s", "run.tpr", "-deffnm", "cpu", backend="cpu")
gmx.mdrun("-s", "run.tpr", "-deffnm", "cuda", backend="cuda")

result = gmx.run("energy", "-f", "auto.edr", "-o", "potential.xvg",
                 input="Potential\n0\n", capture_output=True)
print(result.stdout)
```

`run()` and `mdrun()` accept `cwd`, `capture_output`, `timeout`, and per-process
`env` overrides. Errors raise `subprocess.CalledProcessError` by default.
For separately installed engines, use `Gromacs(cpu=..., cuda=...)`, or set
`GMX_RUNTIME_ROOT` to a directory containing `cpu/bin` and `cuda/bin`.

## WSL

Windows and Linux require separate virtual environments and native binaries:

```bash
cd /mnt/c/Users/Yoshi/projects/gromacs-unified
source ./activate-gromacs-wsl.sh
gmx-unified doctor
gmx-unified --backend cuda mdrun -s run.tpr
```

## Validation and source layout

`source/` contains the library, CLI, build helpers, and tests. The upstream
GROMACS engine is downloaded with a pinned SHA-256 hash into `.native/`.
Generated binaries, virtual environments, and wheels are excluded from Git.
See [validation-logs](validation-logs) for recorded build and validation results.
The tiny argon smoke test compares 21 energy samples from the Python API and CLI;
it does not establish broad scientific accuracy or production performance.

```powershell
python -m unittest discover -s source/tests -v
python source/scripts/smoke_test.py --runtime-root .native/windows/runtime --backend cpu
python source/scripts/smoke_test.py --runtime-root .native/windows/runtime --backend cuda
python source/scripts/smoke_test.py --runtime-root .native/windows/runtime --backend auto
```
