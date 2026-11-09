# Native Windows compatibility changes for GROMACS 2026.4

Apply `windows-2026.4.patch` to the hash-verified upstream release source before
building native Windows engines. The upstream release archive remains unchanged.
These failures reproduced in native upstream test executables without the
Python wrapper.

- `groio.cpp`: backport upstream commit
  [450256fcd1c511c42dc88018b85ee158714717b5](https://github.com/gromacs/gromacs/commit/450256fcd1c511c42dc88018b85ee158714717b5).
  Removes a backward relative seek on a text stream that corrupts GRO trajectory
  reading on Windows. This corrected the analysis, preprocessing, trajectory,
  and simulation test failures observed locally.
- `threefry.h`: apply the old non-constexpr workaround only to MSVC 2015.
  Current MSVC's `std::shuffle` requires a constexpr RNG `min()`. The random
  number generation algorithm and its bounds are unchanged.
- `simd_energy_accumulator.cpp`: generate binary fractions with ten fractional
  bits in the test. The test accumulates at most 128 such values, which remain
  exactly representable in single precision. Previously its serial reference
  sum differed from the SIMD reduction by more than the four-ULP assertion on
  Windows' `rand()` sequence. The strict assertions remain; the production SIMD
  implementation is unchanged.

After these changes, all 86 native Windows CPU CTest suites passed locally.
The unmodified Linux CPU source passed all 94 Linux CTest suites. CUDA results
are recorded separately in the root validation reports.
