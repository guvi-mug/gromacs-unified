# Validation record â€” 8 November 2026

Native Windows and Ubuntu 26.04 under WSL2 were tested on this computer with an NVIDIA GeForce RTX 5080 laptop GPU and Windows driver 592.02 initially; post-reboot CUDA smoke checks passed with driver 621.14.

| Configuration | Build and upstream checks | Python API + CLI |
| --- | --- | --- |
| Native Windows CPU | Passed all 86 CTest suites | Passed CPU mode |
| Native Windows CUDA 13.5 / SM 120 | Passed all 86 CTest suites | Passed CUDA, auto GPU, and auto with GPU hidden |
| WSL Linux CPU / GCC 13.4 | Passed all 94 CTest suites | Passed CPU mode |
| WSL Linux CUDA 13.5 / SM 120 | Passed all 94 CTest suites | Passed CUDA, auto GPU, and auto with GPU hidden |

The Python interface unit suite now has 26 tests, including tampered-download rejection. All 21 potential-energy samples from the Python API and CLI matched in every mode. The final potential was -0.350656 kJ/mol. Native logs confirmed GPU nonbonded work for CUDA/auto and CPU work for forced CPU and hidden-GPU fallback.

Both platform wheels were installed into uv-managed virtual environments. Both engines were discovered without explicit paths. Windows uses Python 3.14.7 and WSL uses Python 3.14.4. The Windows build uses Visual Studio 2026/MSVC 19.51, CMake 4.4.5, static FFTW 3.3.10, and CUDA 13.5. WSL uses GCC 13.4, CMake 4.2.3, system FFTW, and CUDA 13.5.

## Cause of the Windows failures

The failing upstream test executables do not use this Python wrapper.

- GRO trajectory parsing: upstream Windows text-stream seeking bug. Backported upstream commit [450256fcd1c511c42dc88018b85ee158714717b5](https://github.com/gromacs/gromacs/commit/450256fcd1c511c42dc88018b85ee158714717b5).
- Modern MSVC compilation: the upstream RNG header retained a non-constexpr workaround for MSVC 2015. Restricted it to the old compiler. The RNG algorithm is unchanged.
- SIMD energy test: the serial reference sum and SIMD reduction rounded differently on Windows' rand() inputs. The test now uses exactly representable binary fractions; strict assertions and production kernels are unchanged.
- Build helper: our dependency collector needed CUDA's newer bin/x64 location and test-time DLL staging. Both were corrected.

The reproducible patch is `source/patches/windows-2026.4.patch`; details are in `source/patches/README.md`.

## WSL diagnosis

WSL2 Ubuntu runs under user gavi; WslService and vmcompute run normally. The RTX 5080 is visible inside WSL. The earlier E_ACCESSDENIED was observed only in the restricted agent session. No password change or WSL reset was needed.

The first Linux CUDA 12.4 PTX build failed GPU launches with cudaErrorInvalidPtx (218). CUDA 13.1 then hit glibc header incompatibility on Ubuntu 26.04. Installing toolkit 13.5 from NVIDIA's Ubuntu 26.04 repository, specifying its compiler/toolkit paths, and targeting native SM 120 resolved these failures. No Linux display driver was installed inside WSL.

## Source pins and artifacts

GROMACS 2026.4 and FFTW 3.3.10 archives matched the pinned SHA-256 values in `SHA256SUMS` and `source/scripts/fetch_sources.py`. Hashes are checked before extraction, including for cached archives. Windows patches are applied after verification.

Generated artifacts (excluded from Git):

- `wheels/windows-built/gromacs_unified-0.2.0-py3-none-win_amd64.whl`
- `wheels/linux-built/gromacs_unified-0.2.0-py3-none-linux_x86_64.whl`
- `.native/windows/runtime/{cpu,cuda}`
- `.native/linux/runtime/{cpu,cuda}`
- `.venv` and `.venv-wsl`

Detailed local logs (excluded from Git) include `windows-patched-build.log`, `wsl-native-build.log`, `wsl-cuda135-build.log`, `windows-installed-validation.log`, and `wsl-installed-validation.log`. Simulation artifacts are retained in `validation-logs/simulations-windows-installed` and `validation-logs/simulations-linux-installed`.

Reproduce the GPU-host mode matrix with `python source/scripts/validate_modes.py --output validation-logs/simulations-new`. This uses installed package discovery; add `--runtime-root` to test a separate runtime tree. Run `python -m unittest discover -s source/tests -v` for interface tests.

## Scope

The tiny smoke fixture and upstream suites do not establish broad scientific accuracy or production performance. External regression suites subsequently passed on all four engines; full physical validation resumed after the requested reboot and remains in progress. Linux was tested through WSL2, not a separate native Linux boot. The wheels are local native development builds, not a manylinux or universal-system portability claim. Local validation is separate from GitHub Actions runs and published releases.


## Extended validation in progress

The official 2026.4 regression suite passed on all four engines: 42 complex cases per CPU engine, 88 variants per CUDA engine, and 7 essential-dynamics cases per engine. Native Strawberry Perl avoids the MSYS CRLF comparison problem on Windows.

All four configurations completed both public MPI-NAT benchmarks: membrane, 50,000 steps / 100 ps; ribosome, 2,000 steps / 8 ps. Final energy and temperature were finite and no constraint or runtime failures were detected. The CPU benchmark continuation now correctly requests only steps remaining after its checkpoint. Completion does not establish cross-backend accuracy: the initial ribosome potential is -38,003,952 kJ/mol on both CPU builds and approximately -37,924,736 kJ/mol on both CUDA builds. An independent double-precision reference is stable across 4 and 16 threads; it closely matches CUDA and exposes a large mixed-precision CPU energy limitation. See [the investigation and reproduction commands](ribosome-energy-investigation.md).

All four physical-validation jobs resumed after the reboot. Windows CUDA subsequently completed all 46 trajectories and passed analysis of all 14 systems, with no failed checks. All five argon systems passed ensemble and Maxwellâ€“Boltzmann checks in every configuration. Full water-system simulation and final statistical analysis remain pending; no trajectory lengths or thresholds were reduced. Early parallel analyses collided through the upstream parser's fixed temporary filename; isolated reruns cleared those extraction errors. The resume helper now gives each analysis its own current directory.

The published binaries remain a prerelease while three physical suites are incomplete and the large-system CPU energy limitation remains unresolved. Generated raw output remains local; see RESTART.md and EXTENDED_VALIDATION.md for continuation and reproduction.
