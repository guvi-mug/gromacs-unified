# Ribosome initial-energy investigation

The public MPI-NAT ribosome benchmark completed its requested 2,000 steps on all four configurations. A separate same-input, zero-step comparison found a large mixed-precision **CPU energy** sensitivity. This limits the accuracy claim for the published CPU prebuild; successful execution is not sufficient evidence for precise absolute energies on very large systems.

## Measurements

Input: `benchRIB.tpr`, SHA-256 `d8ad9ec4395dea274637f5111ff1996d39c128a356347c1fcdf2553e88ec4f21`, approximately 2.1 million atoms. Each diagnostic starts from this original TPR, without a checkpoint, using `-nsteps 0 -ntmpi 1 -notunepme -pin off -noconfout`.

| Calculation | Threads | Initial potential (kJ/mol) |
| --- | ---: | ---: |
| Windows CPU mixed precision | 4 | -38,003,952.000000 |
| WSL CPU mixed precision | 4 | -38,003,952.000000 |
| Windows CUDA executable, all work explicitly on CPU | 4 | -38,003,952.000000 |
| Windows CPU mixed precision | 16 | -37,951,012.000000 |
| Windows CPU, analytical Ewald instead of tables | 4 | -38,004,192.000000 |
| Windows CUDA, GPU nonbonded / CPU PME | 4 | -37,925,284.000000 |
| Windows and WSL CUDA production run, first frame | 4 | -37,924,736.000000 |
| Independent WSL double-precision CPU reference | 4 | -37,924,799.115135 |
| Independent WSL double-precision CPU reference | 16 | -37,924,799.115016 |
| Diagnostic: double CPU nonbonded scalar accumulators | 4 | -37,925,384.000000 |
| Diagnostic: double CPU nonbonded scalar accumulators | 16 | -37,924,944.000000 |
| Diagnostic: also double CPU PME energy accumulator | 4 | -37,924,844.000000 |
| Diagnostic: also double CPU PME energy accumulator | 16 | -37,924,816.000000 |

The two double-precision results agree within 0.00012 kJ/mol. The four-thread CPU mixed-precision result differs from the double reference by about 79,153 kJ/mol (0.209%). The GPU production-run first frame differs by about 63 kJ/mol (0.00017%). These are observed comparisons, not newly selected acceptance thresholds. Double precision can also change startup constraint rounding, so the comparison is not a bitwise comparison of all intermediate coordinates.

The main differing component is short-range Coulomb energy: CPU four-thread mixed precision -43,643,912; double reference -43,565,220.854547; GPU nonbonded / CPU PME -43,565,200 kJ/mol. CPU reciprocal energy also varies with thread count. Selecting analytical CPU Ewald does not remove the discrepancy.

## Attribution and limits

Direct native `gmx mdrun` commands reproduce the discrepancy without the Python wrapper. Both operating systems agree, and the CUDA executable returns the CPU result when forced to CPU work. The evidence localizes this to native mixed-precision CPU calculation/reduction behavior for this large input. Controlled diagnostic builds then isolated the dominant discrepancy to scalar nonbonded energy accumulation and the smaller discrepancy to PME energy accumulation.

The shipped upstream CPU SIMD accumulator uses `real` scalar energy buffers in `src/gromacs/nbnxm/simd_energy_accumulator.h`. The published production engines were unchanged during this investigation. An [upstream report of thread-sensitive short-range Coulomb energy](https://gitlab.com/gromacs/gromacs/-/issues/4348) describes a similar symptom in an older release; it does not establish that this is the same defect.

This does not by itself demonstrate incorrect forces or failed trajectories. Conversely, finite temperatures, successful completion, and small-system physical-validation passes do not clear this large-system absolute-energy limitation. The release remains a prerelease. Users needing precise large-system absolute energies should validate their own input against a double-precision calculation. The bundled CPU engine uses mixed precision.

## Isolated candidate correction

A separate source copy widened only the two scalar fields `coulombEnergyReal_` and `vdwEnergyReal_` in the CPU SIMD energy accumulator. At four threads this removed more than 99% of the original potential-energy discrepancy, and brought short-range Coulomb energy from -43,643,912 to -43,565,232 kJ/mol (double reference: -43,565,220.854547).

Widening the local PME energy accumulator as a second step moved reciprocal energy from 360,492.906250 to 361,031.531250 kJ/mol (double reference: 361,031.587847). The combined candidate's four-thread potential differs from the double reference by about 45 kJ/mol (0.00012%); at 16 threads it differs by about 17 kJ/mol. This controlled intervention confirms that these upstream CPU energy reductions cause most of the observed discrepancy. The remaining differences include mixed-precision arithmetic and startup constraint rounding.

The exact [experimental patch](../source/patches/experimental-energy-accumulation.patch) is retained for review. It changes scalar energy accumulation only; force and virial code are unchanged. It is **not applied by the builder and is not in v0.2.0 assets**. It has only been built and compared on this WSL CPU diagnostic; it has not passed the full four-configuration test matrix, and the PME Lennard-Jones branch changed by the patch was not exercised by this input. The published CPU limitation therefore remains open. Diagnostic binaries and full double-precision binaries are separate from the running release validation jobs.

## Reproduction

Run native engines directly for custom placement. The wrapper deliberately manages placement flags and rejects conflicting overrides.

```text
gmx mdrun -s benchRIB.tpr -deffnm cpu4 -nsteps 0 -ntmpi 1 -ntomp 4 -pin off -notunepme -noconfout -nb cpu -pme cpu -bonded cpu -update cpu
gmx mdrun -s benchRIB.tpr -deffnm cpu16 -nsteps 0 -ntmpi 1 -ntomp 16 -pin off -notunepme -noconfout -nb cpu -pme cpu -bonded cpu -update cpu
gmx mdrun -s benchRIB.tpr -deffnm gpu -nsteps 0 -ntmpi 1 -ntomp 4 -pin off -notunepme -noconfout -nb gpu -pme cpu -bonded cpu -update cpu
gmx energy -f cpu4.edr -o cpu4.xvg
```

Select `Potential` and `Coulomb-(SR)` interactively in `gmx energy`. Use a CUDA executable for the GPU command. Use separate working directories or distinct output names. Do not append these calculations to production checkpoints.

The independent reference used the original hash-verified Linux GROMACS 2026.4 source, GCC 13.4, system double-precision FFTW, and:

```bash
cmake -S /path/to/gromacs-2026.4 -B build-double-reference -DGMX_DOUBLE=ON -DGMX_GPU=OFF -DGMX_MPI=OFF -DBUILD_TESTING=OFF -DGMX_BUILD_UNITTESTS=OFF -DGMX_FFT_LIBRARY=fftw3 -DGMX_SIMD=AVX2_256 -DGMX_EXTERNAL_BLAS=OFF -DGMX_EXTERNAL_LAPACK=OFF -DCMAKE_C_COMPILER=/usr/bin/gcc-13 -DCMAKE_CXX_COMPILER=/usr/bin/g++-13 -DCMAKE_BUILD_TYPE=Release
cmake --build build-double-reference --parallel 4
```

Repeat the CPU commands with `build-double-reference/bin/gmx_d`, then extract energies with that same double-precision executable. This reference is a diagnostic build, separate from the published prebuilds; it was not subjected to the complete release test matrix.

Local raw output is retained under `.native/energy-diagnosis`, `/home/gavi/gromacs-unified-build/energy-reference`, and `validation-logs/double-reference-*.log`. Generated raw output is excluded from Git.
