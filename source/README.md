# GROMACS Unified — Windows and Linux

A shared Python library and CLI for native CPU/CUDA GROMACS engines.
Supports automatic device selection, explicit CPU/CUDA modes, bundled engines,
and platform-specific native builds on Windows and Linux.

```bash
python -m pip install .
gmx-unified doctor
gmx-unified --backend auto mdrun -s topol.tpr
gmx-unified --backend cpu mdrun -s topol.tpr
gmx-unified --backend cuda mdrun -s topol.tpr
```

```python
from gromacs_unified import Gromacs
Gromacs().mdrun("-s", "topol.tpr", backend="auto")
```

Install an engine-bundled platform wheel for a single package, or use the
Python-only wheel with existing GROMACS installations. Both expose the same
library and CLI. GROMACS detects compatible devices at simulation startup.

Read [UNIFIED.md](UNIFIED.md) for installation, Windows PowerShell/Linux build
commands, engine discovery, Python usage and packaging. [VALIDATION.md](VALIDATION.md)
records actual checks and remaining platform validation. Native Windows and
WSL Linux CPU/CUDA builds and Python/CLI simulations were validated locally
on 8 November 2026. See the repository-level README and installation guide.

The original Windows release documentation is preserved in
[WINDOWS_LEGACY.md](WINDOWS_LEGACY.md). The existing upstream releases remain
unchanged. This project does not modify GROMACS numerical kernels.
