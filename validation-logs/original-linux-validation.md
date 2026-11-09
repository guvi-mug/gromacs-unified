# Validation record

Development validation performed on 8 November 2026 in a Linux x86-64 workspace.
Workflows have not been dispatched on Windows or NVIDIA GPU runners. Workflow
files are not evidence of successful native builds on those systems.

| Check | Observed result |
| --- | --- |
| Python unit tests | 22 passed: selection, CLI, discovery, environment, build plans, staging |
| Source retrieval | GROMACS 2026.4 and FFTW 3.3.10 archives verified and extracted using pinned SHA-256 hashes |
| FFTW native build | Static single-precision library compiled; benchmark verification passed for 32x64 and ib256 |
| GROMACS native build | Linux x86-64 CPU engine compiled and installed using internal FFTPACK and SSE2 |
| CPU integration | Python and CLI each completed 20 MD steps; all 21 potential-energy samples matched |
| Automatic integration | Completed using CPU on this host; Python and CLI energy samples matched |
| Native wheel | Built gromacs_unified-0.2.0-py3-none-linux_x86_64.whl with independent CPU runtime |
| Python-only wheel | Fresh-venv install passed all 22 interface tests; current module bytes match source |
| Wheel relocation | Installed into a fresh venv with spaces in its path; bundled engine discovered and CPU simulation passed |
| Workflow/config syntax | Three YAML workflows parsed; Python compilation, shell syntax and git whitespace checks passed |
| Native Windows CPU/CUDA | Build and dependency-collection implementation present; execution pending matching runner |
| Native Linux CUDA/GPU | Execution pending CUDA toolkit/GPU host |

Final potential energy for the smoke simulation was -0.350656 kJ/mol. This
small integration fixture does not establish broad scientific accuracy or
production performance.

The included Linux wheel is a development artifact. Full upstream unit and
regression suites were not run for it (`checks_passed: false` in its build
manifest). The native workflow runs the upstream unit-check target before
staging; regression-suite and hardware validation remain release work. It is
not a manylinux portability claim: the binary was built with GCC 13 on this
Ubuntu 24.04-compatible host and may require matching system runtime libraries.

Source inputs and build flags are recorded in the scripts and bundled build
manifest. No native Windows wheel or CUDA-enabled wheel is included in this
local download, and no GitHub release has been published.
