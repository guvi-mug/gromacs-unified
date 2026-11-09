# Installation

Use uv for Python management. The Python package needs Python 3.10 or newer;
the source-download helper needs Python 3.12 or newer. Run all commands below
from the repository root. Windows and Linux need separate environments and
engine builds, even when Linux runs under WSL on the same computer. The native
build helper passes its current Python interpreter to CMake, so invoke it from
the activated uv environment.

## Install a prebuilt release

Download the wheel for your OS, `smoke-test.zip`, and release `SHA256SUMS` from
[v0.2.0 assets](https://github.com/guvi-mug/gromacs-unified/releases/tag/v0.2.0).
Release assets contain large binaries; Git history contains their source and
reproducible build instructions. The release checksum file covers the binary
assets. The repository-root `SHA256SUMS` covers the upstream source archives.

These prebuilds are a **prerelease**. A large ribosome input exposed a mixed-precision CPU absolute-energy limitation; see the [measured comparison and reproduction commands](validation-logs/ribosome-energy-investigation.md). Full Windows and WSL CUDA physical validation passed; the two CPU physical suites are still in progress. See the [validation record](source/VALIDATION.md) for current scope.

These wheels bundle both engines and the FFTW/cuFFT libraries. A compiler,
CMake, or full CUDA Toolkit is not needed to use them. Python 3.10+ is needed;
the examples use uv-managed Python 3.14.

### Prebuilt native Windows

Use Windows 10/11 x64. Install the latest
[Microsoft Visual C++ v14 x64 Redistributable](https://aka.ms/vc14/vc_redist.x64.exe)
as described in [Microsoft's runtime guidance](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist).
The runtime must be at least as recent as the Visual Studio 2026 build tools.
Install uv if it is not already available, then in your download directory:

```powershell
Get-FileHash ./gromacs_unified-0.2.0-py3-none-win_amd64.whl -Algorithm SHA256
# Compare with the matching entry in the downloaded release SHA256SUMS.
uv venv --python 3.14 .venv
. .\.venv\Scripts\Activate.ps1
uv pip install ./gromacs_unified-0.2.0-py3-none-win_amd64.whl
gmx-unified doctor
```

For a globally available CLI managed by uv instead of a project venv:

```powershell
uv tool install --python 3.14 ./gromacs_unified-0.2.0-py3-none-win_amd64.whl
uv tool update-shell
```

Open a new terminal after updating PATH. Use the venv installation when you
want to import the library from your own Python program.

### Prebuilt Linux and Windows WSL2

Use the Linux wheel inside WSL2, not the Windows wheel. The Linux asset requires
glibc **2.43 or newer**, C++ runtime symbol version **GLIBCXX_3.4.32 or newer**,
and OpenMP (`libgomp.so.1`). It was built and tested on Ubuntu 26.04. It is not
compatible with an unmodified Ubuntu 22.04/24.04 userspace. Build from source on
older distributions instead of replacing the system's glibc manually.

```bash
ldd --version
sudo apt-get install -y libstdc++6 libgomp1
sha256sum -c SHA256SUMS --ignore-missing
uv venv --python 3.14 .venv
source .venv/bin/activate
uv pip install ./gromacs_unified-0.2.0-py3-none-linux_x86_64.whl
gmx-unified doctor
```

`uv tool install --python 3.14 ./gromacs_unified-0.2.0-py3-none-linux_x86_64.whl`
and `uv tool update-shell` provide a global CLI on Linux too.

### Prebuilt GPU setup and first simulation

The CUDA engines in these assets target **SM 120 / RTX 50-series**. Other GPU
architectures require a source build with the appropriate architecture. A
compatible NVIDIA driver is required; these builds passed on driver 592.02.
In WSL2, install/update that driver on Windows and confirm `nvidia-smi` works
inside WSL. No Linux display driver or full CUDA Toolkit is required for the
bundled wheel. CPU mode works without an NVIDIA GPU.

Extract `smoke-test.zip`, change into the extracted `smoke-test` directory, then:

```bash
gmx-unified grompp -f md.mdp -c conf.gro -p topol.top -o run.tpr
gmx-unified --backend cpu mdrun -s run.tpr -deffnm cpu -ntmpi 1 -ntomp 1
gmx-unified --backend auto mdrun -s run.tpr -deffnm auto -ntmpi 1 -ntomp 1
gmx-unified --backend cuda mdrun -s run.tpr -deffnm cuda -ntmpi 1 -ntomp 1
```

The final command requires a supported visible GPU. Inspect the native run
logs for actual device selection; `doctor` alone establishes engine loadability.
See [README.md](README.md#python-library) for Python API examples. Bundled
licenses and build manifests are installed under the package's `runtime/` tree.

## Pinned source downloads

The downloader uses the exact release URLs and verifies SHA-256 before
extracting anything. It also rechecks cached archives. A changed or corrupted
archive is rejected; it never falls back to a different version or to `latest`.
The downloaded archives on this machine matched both pins:

| Source | Release | SHA-256 |
| --- | --- | --- |
| GROMACS | 2026.4 | `58eda60979b124fcf9dff8b1b63cedfbc72fdb36d99e921dc1bdc310571098b6` |
| FFTW | 3.3.10 | `56c932549852cddcfafdab3820b0200c7742675be92179e59e6215b340e26467` |

The pins live in `source/scripts/fetch_sources.py`. Windows compatibility
patches are applied after archive verification and are tracked in
`source/patches/windows-2026.4.patch`.

## Native Windows

Install Git, uv, CMake 3.28 or newer, and Visual Studio C++ Build Tools with the
Windows SDK. For CUDA, install a CUDA Toolkit compatible with your compiler,
GPU, and NVIDIA driver. This machine uses Visual Studio 2026 and CUDA 13.5.
Open an **x64 Native Tools Command Prompt**, then start PowerShell from it so
that `cl` and the SDK are available. Keep CUDA's `bin` directory on PATH.

After installing the prerequisites, the automatic builder can discover Visual
Studio, create the uv environment, download and patch the engine, build and
check the available engines, and install one bundled package:

```powershell
./Build-Gromacs.ps1
# Or force a CPU-only build:
./Build-Gromacs.ps1 -Backend cpu
```

It chooses CPU plus CUDA when a toolkit is available, otherwise CPU only.
`-CudaArchitectures 120` selects the RTX 5080 explicitly; the default is the
local GPU's native architecture. The manual equivalent follows:

```powershell
uv venv --python 3.14 .venv
. .\.venv\Scripts\Activate.ps1
uv pip install -e ./source ninja
$env:CMAKE_GENERATOR = 'Ninja'
python source/scripts/fetch_sources.py gromacs --destination .native/sources
python source/scripts/fetch_sources.py fftw --destination .native/sources
$patch = (Resolve-Path source/patches/windows-2026.4.patch).Path
git -C .native/sources/gromacs-2026.4 apply --check $patch
git -C .native/sources/gromacs-2026.4 apply $patch
python source/scripts/build_fftw.py .native/sources/fftw-3.3.10 .native/windows/fftw --work .native/windows/fftw-build --jobs 8
python source/scripts/build_native.py .native/sources/gromacs-2026.4 .native/windows/runtime --backend both --fftw-prefix .native/windows/fftw --work .native/windows/build --generator Ninja --jobs 8 --cmake-arg=-DGMX_CUDA_ARCHITECTURES=120
. ./Activate-Gromacs.ps1
gmx-unified doctor
```

Architecture `120` targets the RTX 5080 used here. Select the appropriate
architecture for another GPU, or omit the architecture argument to let GROMACS
choose its supported architecture set. To build CPU only, use `--backend cpu`
and omit the CUDA architecture argument. Apply the Windows patch once to a
fresh release extraction; see [patch details](source/patches/README.md).
The source downloader refuses to overwrite an existing extracted source tree.

The native builder runs upstream checks before installation. Do not treat a
failed check as a successful validated build. The Windows compatibility patch
is required with the tested modern compiler and release source.

Add the launcher to your **user PATH**, and enable automatic venv activation
when entering this checkout in PowerShell:

```powershell
./scripts/setup-user.ps1
```

Open a new PowerShell terminal. `gmx-unified` then works from any directory.
Entering the project directory activates its uv venv at the next prompt;
leaving deactivates an environment activated by this hook. Another existing
active environment is preserved. The setup changes per-user PowerShell
profiles, preserving existing content and backing up profiles before updates.
To undo it, remove this checkout's `bin` from user PATH and remove the GROMACS
dot-source line from the user profiles under Documents/WindowsPowerShell and
Documents/PowerShell. No administrator account is needed for this setup.

## Windows with WSL2

In Windows PowerShell, inspect WSL and GPU visibility:

```powershell
wsl --list --verbose
wsl --status
wsl -d Ubuntu -- nvidia-smi
```

If Ubuntu is not installed, use `wsl --install -d Ubuntu` and complete its
first-run setup. Use a WSL2 distribution. An `E_ACCESSDENIED` from a restricted
agent session does not prove WSL itself is broken; retry from a normal terminal.
This machine's Ubuntu runs as `gavi`; its WSL service and GPU access work.

Inside Ubuntu, install the Linux prerequisites listed below. For best filesystem
performance, clone into your Linux home directory. Alternatively, this checkout
is accessible at `/mnt/c/Users/Yoshi/projects/gromacs-unified`. Never activate the
Windows `.venv` from Linux. Use `.venv-wsl`:

```bash
curl -LsSf https://astral.sh/uv/install.sh -o /tmp/uv-install.sh
sh /tmp/uv-install.sh
export PATH="$HOME/.local/bin:$PATH"
uv venv --python 3.14 .venv-wsl
source .venv-wsl/bin/activate
uv pip install -e ./source
```

Follow the Linux engine build commands below, then:

```bash
source ./activate-gromacs-wsl.sh
gmx-unified doctor
```

CUDA in WSL uses the Windows NVIDIA driver. Install the Linux CUDA **toolkit**
inside WSL, without installing a Linux display driver. See NVIDIA's
[CUDA on WSL guide](https://docs.nvidia.com/cuda/wsl-user-guide/index.html) and
[Linux toolkit installation guide](https://docs.nvidia.com/cuda/cuda-installation-guide-linux/).
Choose a toolkit that supports the Linux distribution as well as the GPU. The
old CUDA 12.4 PTX build failed GPU kernel launches on this machine. CUDA 13.1
also encountered a glibc header incompatibility on Ubuntu 26.04. Native-target
validation with a toolkit supporting Ubuntu 26.04 is recorded in the validation
report; do not infer successful GPU execution from `nvidia-smi` alone.

## Linux

On Ubuntu, install build tools and single-precision FFTW:

```bash
sudo apt-get update
sudo apt-get install -y build-essential cmake ninja-build python3-venv libfftw3-dev
curl -LsSf https://astral.sh/uv/install.sh -o /tmp/uv-install.sh
sh /tmp/uv-install.sh
export PATH="$HOME/.local/bin:$PATH"
uv venv --python 3.14 .venv
source .venv/bin/activate
uv pip install -e ./source
python source/scripts/fetch_sources.py gromacs --destination .native/sources
python source/scripts/build_native.py .native/sources/gromacs-2026.4 .native/linux/runtime --backend cpu --fftw-prefix /usr --work .native/linux/build --generator Ninja --jobs 8
export GMX_RUNTIME_ROOT="$PWD/.native/linux/runtime"
gmx-unified doctor
```

Use the already activated `.venv-wsl` instead of creating `.venv` when following
these steps in a shared Windows checkout. On another distribution, install
equivalent compiler, CMake, Ninja, and FFTW development packages. Check
`cmake --version`; upgrade it if it is older than 3.28.

For CUDA, install a compatible NVIDIA driver on native Linux and a CUDA Toolkit.
Set paths to your installed toolkit. Example for CUDA 13.5 and an RTX 5080:

```bash
export PATH="/usr/local/cuda-13.5/bin:$PATH"
export CC=gcc-13 CXX=g++-13
python source/scripts/build_native.py .native/sources/gromacs-2026.4 .native/linux/runtime --backend cuda --fftw-prefix /usr --work .native/linux/cuda-build --generator Ninja --jobs 6 --cmake-arg=-DGMX_CUDA_ARCHITECTURES=120 --cmake-arg=-DCUDAToolkit_ROOT=/usr/local/cuda-13.5 --cmake-arg=-DCMAKE_CUDA_COMPILER=/usr/local/cuda-13.5/bin/nvcc
```

Install the selected compiler if necessary. Keep the compiler within the CUDA
Toolkit's supported range. Explicit toolkit paths avoid accidentally mixing a
distribution-provided CUDA installation with a newer toolkit. A fresh build
directory is recommended when changing toolkits.

For global Linux CLI access without globally selecting this project's Python:

```bash
mkdir -p "$HOME/.local/bin"
project_root="$PWD"
venv_python="$VIRTUAL_ENV/bin/python"
printf '#!/bin/sh\nexport GMX_RUNTIME_ROOT="%s/.native/linux/runtime"\nexec "%s" -m gromacs_unified "$@"\n' "$project_root" "$venv_python" > "$HOME/.local/bin/gmx-unified"
chmod +x "$HOME/.local/bin/gmx-unified"
```

Keep `~/.local/bin` on PATH. Recreate the launcher if you move the checkout.

## Verify CLI and Python

Use `windows` or `linux` in the runtime path as appropriate:

```bash
python -m unittest discover -s source/tests -v
python source/scripts/smoke_test.py --runtime-root .native/linux/runtime --backend cpu
python source/scripts/smoke_test.py --runtime-root .native/linux/runtime --backend cuda
python source/scripts/smoke_test.py --runtime-root .native/linux/runtime --backend auto
```

Each smoke test runs a real simulation through Python and the CLI and compares
their potential energy samples. CUDA mode forces GPU nonbonded computation.
CPU mode and automatic fallback must remain usable when no GPU is visible.
See [README.md](README.md) for CLI and Python examples.

On a GPU host, retain simulation artifacts and assert GPU selection plus CPU
fallback with:

```bash
python source/scripts/validate_modes.py --runtime-root .native/linux/runtime --output validation-logs/simulations-local
```

Choose a new output directory for every run. Omit `--runtime-root` to validate
automatic discovery from an installed engine-bundled wheel.

## Bundle engines into one installable package

The packaging helper copies the source into a temporary directory, stages the
checked engines, bundles FFTW/cuFFT libraries on Linux, and builds a wheel:

```bash
python source/scripts/package_native.py .native/linux/runtime --out dist --install
```

Use `.native/windows/runtime` on Windows. Linux packaging needs `ldd` and
`readelf` from the native build environment. `--install` installs the result
into the Python environment running the helper. The Linux manifest records
the bundled library hashes and required system ABI versions.

For lower-level staging without automatic Linux library collection:

From a clean copy of `source/` on the build OS, stage its runtime and build a
platform wheel. The destination runtime directory must not already exist:

```bash
python source/scripts/stage_runtime.py .native/linux/runtime --destination source/src/gromacs_unified/runtime
uv build --wheel ./source --out-dir dist
```

Use `.native/windows/runtime` on Windows. Keep Linux and Windows staging trees
separate; their engines cannot share a platform wheel. Install the resulting
wheel with `uv pip install /path/to/package.whl`. The installed `gmx-unified`
then discovers both engines automatically, with no `GMX_RUNTIME_ROOT` required.
Only package engines whose upstream checks passed. This is a native platform
build, not a manylinux portability certification.
