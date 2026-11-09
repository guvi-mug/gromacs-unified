# GROMACS Unified 0.2.0 development package

> This file describes the original input ZIP. For the current checkout,
> native Windows/WSL builds, usage, and installation, start with [README.md](README.md)
> and [INSTALLATION.md](INSTALLATION.md). The original archive checksum list is
> retained under `validation-logs/original-package-SHA256SUMS.txt`.

This ZIP includes the full project source, a tested Linux x86-64 CPU wheel,
and a Python-only wheel usable with existing Windows or Linux engines.

## Try the Linux CPU package

From this extracted directory on a compatible Linux x86-64 machine:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install wheels/linux/gromacs_unified-0.2.0-py3-none-linux_x86_64.whl
python -m gromacs_unified doctor
python source/scripts/smoke_test.py --backend cpu
python -m gromacs_unified --backend cpu mdrun -s /path/to/topol.tpr
```

This wheel includes its CPU engine and data. It was built on an Ubuntu
24.04-compatible x86-64 host, uses SSE2 and internal FFTPACK, and depends on
compatible system C/C++ and OpenMP runtime libraries. It is a development build;
full upstream unit/regression checks were not run.

## Windows and existing engine installations

Use Python 3.10+ to install the shared interface:

```powershell
py -m pip install wheels/interface/gromacs_unified-0.2.0-py3-none-any.whl
py -m gromacs_unified --cpu-executable "C:\gromacs-cpu\bin\gmx.exe" --backend cpu mdrun -s topol.tpr
py -m gromacs_unified --cuda-executable "C:\gromacs-cuda\bin\gmx.exe" --backend cuda mdrun -s topol.tpr
```

Or build both engines using the instructions in source/UNIFIED.md. Bundled
platform builds discover cpu/ and cuda/ installations automatically. The Python
API works on both OSes:

```python
from gromacs_unified import Gromacs

gmx = Gromacs(cpu=r"C:\gromacs-cpu\bin\gmx.exe", cuda=r"C:\gromacs-cuda\bin\gmx.exe")
gmx.mdrun("-s", "topol.tpr", backend="auto")
```

The Python-only wheel does not include native engines. No compiled native
Windows wheel or CUDA-enabled wheel is included: those builds and hardware
checks require matching runners. CUDA mode requires a compatible NVIDIA GPU
and driver. Windows requires the compatible Microsoft Visual C++ runtime.

## Project contents

- source/: Python library/CLI, Windows/Linux native builders, source downloader,
  packaging tools, test fixtures, and GitHub workflows.
- wheels/linux/: CPU engine plus library and CLI in one package.
- wheels/interface/: portable Python library and CLI for separately installed engines.
- validation-logs/: observed package checks.
- SHA256SUMS: hashes of the included files.

Read source/VALIDATION.md for the exact validation scope and remaining release
work. CPU and automatic Linux simulations passed, including installation into
a fresh virtual environment and matching Python/CLI energy outputs. Windows and
CUDA runtime execution are not yet validated. This download has not been
published as a GitHub release.
