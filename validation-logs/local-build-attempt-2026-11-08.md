# Local build and test attempt — 2026-11-08

No native builds or simulation tests completed in this session.

| Requested configuration | Result | Blocker |
| --- | --- | --- |
| Native Windows CPU | Blocked | No usable Python, CMake, or C++ compiler found; upstream GROMACS source absent |
| Native Windows CUDA | Blocked | Windows prerequisites above plus CUDA toolkit/nvcc not found |
| WSL Linux CPU | Blocked | wsl --list --verbose returns Wsl/EnumerateDistros/Service/E_ACCESSDENIED |
| WSL Linux CUDA | Blocked | WSL access denied; Linux toolkit and GPU access could not be inspected |

Observed hardware: nvidia-smi succeeds, NVIDIA GeForce RTX 5080 laptop GPU, 16303 MiB VRAM, driver 592.02. Its CUDA Version 13.1 field reports driver compatibility and does not establish an installed CUDA compiler.

The python command resolves to the WindowsApps alias and fails with 'The file cannot be accessed by the system'. No Python installation was found in the checked local Programs or Scoop directories. CMake, Ninja, cl, and nvcc were not found on PATH. Standard CMake, Visual Studio, and CUDA installation locations checked were absent.

Attempted a workspace-local Python 3.12 installation with uv, with cache and installation paths under .tools/. Download failed after retries with socket permission error 10013. This session cannot request broader sandbox access under its configured approval policy.

Next execution requires a session with working WSL service access and network access or preinstalled tools. Native Windows needs Python 3.12+, MSVC x64 build tools, CMake, FFTW, and a CUDA toolkit compatible with the engine/GPU. Retrieve pinned upstream sources using source/scripts/fetch_sources.py. Use source/scripts/build_native.py with checks enabled for separate cpu and cuda builds, then run source/scripts/smoke_test.py for each backend. Perform the equivalent builds and smoke tests inside WSL. Existing validation records in this package describe earlier Linux CPU work, not successful tests on this machine.

## Recheck at 17:17 local time

CMake 4.4.5 now runs successfully. Visual Studio 18 Community MSVC compiler files are now present (including Hostx64/x64). CUDA v13.5 directory is now present, but no nvcc.exe was found beneath it during this check. The NVIDIA GPU remains visible. Python still resolves to an inaccessible WindowsApps alias; retrying workspace-local Python installation failed with socket permission error 10013. WSL enumeration still fails with E_ACCESSDENIED. No engine builds or tests completed on this recheck.
Follow-up: CUDA compiler files appeared during the recheck; see the compiler version result from the final probe. The prior missing-nvcc observation may reflect installation still in progress.

## uv Python follow-up

uv run --no-project --offline --python 3.14 python --version succeeds with Python 3.14.7 from the existing uv-managed installation. Global Python is not needed. The earlier Python blocker is resolved.

Running the pinned GROMACS downloader through that uv Python failed with urllib.error.URLError caused by WinError 10013 (socket access denied). No engine archive downloaded. Local interface test output is recorded in windows-interface-tests.log; these tests do not validate native engines or GPU execution.
