# Validation record

Local native Windows and WSL2 Linux CPU/CUDA builds passed on 8 November 2026 with an NVIDIA RTX 5080 laptop GPU.

| Configuration | Upstream CTest suites | Python API / CLI modes |
| --- | --- | --- |
| Native Windows CPU | 86 passed | CPU |
| Native Windows CUDA 13.5 | 86 passed | CUDA, auto GPU, auto CPU fallback |
| WSL Linux CPU | 94 passed | CPU |
| WSL Linux CUDA 13.5 | 94 passed | CUDA, auto GPU, auto CPU fallback |

The interface suite has 26 tests. All 21 energy samples matched between Python and CLI in every simulation mode, ending at -0.350656 kJ/mol. GPU selection and CPU fallback were verified from native logs. Both platform wheels were installed into uv environments and discovered both engines without explicit paths.

Windows needed the tracked [upstream compatibility patches](patches/README.md). The build helper also needed updated CUDA DLL discovery. WSL uses toolkit 13.5 with explicit toolkit/compiler paths and native SM 120; older toolkit attempts failed and are documented in the report.

See [the full local validation report](../validation-logs/native-validation-2026-11-08.md) for tooling, artifacts, root causes, and limits. The original input ZIP's Linux-only record is retained in `validation-logs/original-linux-validation.md` at the repository root.

External regression suites passed on all four engines. After the requested reboot, NVIDIA driver 621.14 passed both CUDA smoke tests. All eight large benchmark runs completed: each OS/backend finished the 50,000-step membrane (100 ps) and 2,000-step ribosome (8 ps) simulations with finite energies and temperatures and no constraint failures. The ribosome initial CPU/CUDA potential energies differ by approximately 0.21%; a controlled native-engine comparison is investigating this difference. Completion is not a cross-backend accuracy pass.

The four full physical-validation suites are still running with their original trajectory lengths and statistical thresholds. All five argon systems passed their ensemble and Maxwell–Boltzmann checks in each configuration; complete water-system analysis remains pending. These wheels remain a prerelease. Linux testing used WSL2 on this computer, not a separate Linux boot; the wheels are not universal portability claims. See [the restart handoff](../RESTART.md) for runtime locations and continuation commands.
