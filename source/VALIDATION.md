# Validation record

Local native Windows and WSL2 Linux CPU/CUDA builds passed on 8 November 2026 with an NVIDIA RTX 5080 laptop GPU.

| Configuration | Upstream CTest suites | Python API / CLI modes |
| --- | --- | --- |
| Native Windows CPU | 86 passed | CPU |
| Native Windows CUDA 13.5 | 86 passed | CUDA, auto GPU, auto CPU fallback |
| WSL Linux CPU | 94 passed | CPU |
| WSL Linux CUDA 13.5 | 94 passed | CUDA, auto GPU, auto CPU fallback |

The interface suite has 23 tests. All 21 energy samples matched between Python and CLI in every simulation mode, ending at -0.350656 kJ/mol. GPU selection and CPU fallback were verified from native logs. Both platform wheels were installed into uv environments and discovered both engines without explicit paths.

Windows needed the tracked [upstream compatibility patches](patches/README.md). The build helper also needed updated CUDA DLL discovery. WSL uses toolkit 13.5 with explicit toolkit/compiler paths and native SM 120; older toolkit attempts failed and are documented in the report.

See [the full local validation report](../validation-logs/native-validation-2026-11-08.md) for tooling, artifacts, root causes, and limits. The original input ZIP's Linux-only record is retained in `validation-logs/original-linux-validation.md` at the repository root.

External regression suites passed on all four engines. The full physical-validation suite is currently running. These local native development wheels are not universal portability claims, and the small fixture does not establish production performance or broad scientific accuracy. Linux testing used WSL2 on this computer. Local checks are separate from GitHub Actions runs and release publication.
