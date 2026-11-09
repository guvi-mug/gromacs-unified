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

External regression suites passed on all four engines: each CPU engine passed 42 complex + 7 essential-dynamics cases; each CUDA engine passed 88 complex variants + 7 essential-dynamics cases.

Full upstream physical validation also passed on all four configurations. Each completed 46/46 trajectories, all 14 systems, and all 24 primary checks: 184 trajectories and 96 primary checks overall. Original lengths, seeds, and thresholds were retained. See [structured results](../validation-logs/physical-validation-results.json).

All eight public MPI-NAT benchmark runs completed: each OS/backend finished the 50,000-step membrane (100 ps) and 2,000-step ribosome (8 ps) simulations with finite energies and temperatures and no detected constraint/runtime failures. Exact final steps and input hashes are in [benchmark-results.json](../validation-logs/benchmark-results.json). Timings came from shared load and are not isolated performance comparisons.

The release remains a **prerelease** because the large ribosome input exposed a mixed-precision CPU absolute-energy limitation. A stable double-precision reference found a 0.209% difference for the four-thread CPU initial potential; CUDA differed by about 0.00017%. Controlled diagnostic builds traced most of the gap to upstream CPU energy accumulation. The [experimental correction](patches/experimental-energy-accumulation.patch) is separate from the published assets and has not passed the release matrix. See [the investigation](../validation-logs/ribosome-energy-investigation.md).

These physical passes do not clear that larger-system limitation or establish accuracy for every input. Linux testing used WSL2 on this computer, not a separate Linux boot, and the wheels are not universal portability claims. Post-reboot CUDA smoke checks passed with driver 621.14. CMake now uses the invoking uv Python; all 26 interface/helper tests pass on Windows and WSL.
