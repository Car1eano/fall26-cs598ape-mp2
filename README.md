# 598APE-HW2

## MP2 performance experiments

Baseline commit: `f19cc633664c9a333b208049770424d58d14909e`.
The measured machine is the course VM `fa26-cs598a-048.cs.illinois.edu`, with
4 vCPUs (Intel Xeon Silver 4216), about 16 GiB RAM, Ubuntu 26.04.1 and G++ 15.2.0.
Full environment records are in [results/environment](results/environment).

Build, run and benchmark commands, changes and pending checks are listed below.
Saved statistics and charts: [results table](results/summary.md),
[runtime](results/runtime.png), [speedup](results/speedup.png).
Five-workload overview: [table](results/all-summary.md),
[runtime](results/all-runtime.png), [speedup](results/all-speedup.png).

| Change | File | Commit | Recorded experiment |
|---|---|---|---|
| Original baseline | — | `f19cc633664c9a333b208049770424d58d14909e` | `baseline` |
| Enable `-O2` | `Makefile` | `e453776` | `o2` (same original source, explicit `-O2`) |
| Direct stack indexing | `src/reg_stack.h` | `cbc92ec` | `stack` (original flags), `o2-stack` (combined) |
| Stable index sorting | `benchmark/genetic_benchmark.cpp` | `a150e4f` | `sorted` |
| Free replaced hoist nodes | `src/program.cpp` | `4850ad7` | `hoist-fixed` |
| Fix integer range overflow | `include/custom_distributions.h` | `5132428` | `final` |

Direct stack indexing removes the slot-scanning loops in push/pop. The original
Diabetes gprof profile attributed 46.11% self time to push and 6.67% to pop.
Sorting indices avoids repeated deep copies of programs: total Cancer program
assignments decreased from 65,190,213 to 329,285 in the saved profiles. Profile
records are in `results/profile-baseline`, `results/profile-o2-stack-cancer` and
`results/profile-sorted-cancer`. Profiling times are excluded from benchmarks.
The hoist cleanup and integer-range changes fix memory/undefined-behavior issues;
small timing differences after sorting are not evidence of additional speedup.

### Build and run

Required for the three CSV benchmarks: a C++17 compiler, make, Git, tar and
Python 3. For diagnostics: binutils (`gprof`), Valgrind and GCC sanitizer support;
perf is optional when the host permits it. Racket is only needed to run the
exported Racket programs or render images. Docker is optional.

On Ubuntu, these packages cover builds and diagnostics:

```bash
sudo apt-get update
sudo apt-get install g++ make git tar binutils python3 python3-venv valgrind gdb racket
```

Clean before rebuilding after source/header/flag changes:

```bash
make clean
make -j2
./genetic_benchmark diabetes
./genetic_benchmark cancer
./genetic_benchmark housing
mkdir -p results/images
./genetic_benchmark silk-wave > results/images/silk.rkt
racket results/images/silk.rkt results/images/silk.png
./genetic_benchmark square-wave > results/images/square.rkt
racket results/images/square.rkt results/images/square.png
```

### Benchmarks

To reproduce the independent compiler and stack experiments, run the following
from the repository root. Each command archives the original commit into a fresh,
ignored `results/<label>/source` directory. Labels must be new; existing results
are never overwritten. No checkout/reset is needed, and working-tree changes are
preserved. Flags are explicit: the harness default is the original unoptimized
flags even when archiving a later commit.

```bash
python3 tools/benchmark.py --label baseline-repeat
python3 tools/benchmark.py --label o2-repeat '--flags=-std=c++17 -O2 -Wall -Wextra -I include -I.'
python3 tools/benchmark.py --label stack-repeat --stack-candidate
python3 tools/benchmark.py --label o2-stack-repeat --stack-candidate '--flags=-std=c++17 -O2 -Wall -Wextra -I include -I.'
python3 tools/benchmark.py --ref a150e4f --label sorted-repeat '--flags=-std=c++17 -O2 -Wall -Wextra -I include -I.'
python3 tools/benchmark.py --ref 4850ad7 --label hoist-fixed-repeat '--flags=-std=c++17 -O2 -Wall -Wextra -I include -I.'
python3 tools/benchmark.py --ref 5132428 --label final-repeat '--flags=-std=c++17 -O2 -Wall -Wextra -I include -I.'
```

All use the original CSV data, deterministic split, function sets, populations,
generations, seeds and stopping criteria. Each dataset gets one warmup and three
measured runs. Runs are sequential. Raw stdout, stderr, internal time, external
wall time, build warnings, source/data hashes and flags are retained.
The summary uses medians, min–max, means and sample standard deviations; speedup
uses internal-time medians. Same-seed repeats measure timing variability, not
cross-seed quality. The VM shares its host and has background services.

### Tables and figures

Plotting requires Python with the packages in `tools/plot-requirements.txt`:

```bash
python3 -m venv /tmp/mp2-plots
/tmp/mp2-plots/bin/pip install -r tools/plot-requirements.txt
/tmp/mp2-plots/bin/python tools/summarize.py baseline o2 stack o2-stack sorted hoist-fixed final
# Regenerate all saved CSV/image tables and figures after checking their records:
/tmp/mp2-plots/bin/python tools/summarize_all.py
```

If system Python lacks `venv`/`ensurepip`, install `python3-venv` or use
`uv venv /tmp/mp2-plots` and `uv pip install --python /tmp/mp2-plots/bin/python -r tools/plot-requirements.txt`.
The summary checks raw output hashes, recorded timings, repeat counts, dataset
hashes and baseline output with timing lines removed before writing tables or
standalone PNG/SVG charts. Invalid or inconsistent batches are rejected before
existing artifacts are changed.
The CSV figures include all seven recorded stages. The overview compares
baseline with final for all five workloads; intermediate image stages were not
measured. Bars show medians; runtime whiskers show the observed min–max, not a
confidence interval. Both PNG and SVG versions are saved. All 100 runs were
checked (75 measured runs and 25 warmups). Tool checks can be repeated with:

```bash
python3 -m unittest discover -s tests -p '*_test.py'
```

These commands validate saved records and regenerate figures; they do not rerun
training. Use the benchmark commands above and below to collect new timings.

### Profiling and correctness

For hotspot evidence and independent correctness checks:

The source paths below are created by the full benchmark commands above;
source archives are not included in Git. Run those commands first, or use
`results/verify-baseline/source` and `results/verify-final/source` after the
single-run procedure below.

```bash
perf stat -e task-clock true
python3 tools/profile.py --source results/baseline-repeat/source --label profile-repeat --optimization=-O0
python3 tools/check.py --source results/baseline-repeat/source --label check-repeat --optimization=-O0
python3 tools/check.py --source results/o2-stack-repeat/source --label check-sanitized-repeat --sanitize
python3 tools/check.py --source results/final-repeat/source --label check-final-repeat --sanitize --sorting --mutations --distributions
python3 tools/profile.py --source results/o2-stack-repeat/source --label profile-cancer-repeat --dataset cancer --optimization=-O2
python3 tools/profile.py --source results/sorted-repeat/source --label profile-sorted-repeat --dataset cancer --optimization=-O2
python3 tools/memory.py --ref 5132428 --label memory-asan-repeat --mode sanitize --datasets diabetes cancer housing
python3 tools/memory.py --ref 5132428 --label memory-valgrind-repeat --mode valgrind
```

This VM blocks perf (`perf_event_paranoid=4`); its error is saved. The gprof
fallback builds with `-pg -g`, and profiling times are excluded from benchmark
statistics. Independent tests check stack boundaries and 1000 generated trees
against a recursive evaluator, including operand order and protected-log inputs.
Sorting checks cover stable ties, NaNs, infinities, empty inputs and ownership.
A repeated mutation check exercises the output slot that previously leaked.

The original source has a confirmed hoist-mutation leak. Its full-workload
Valgrind log is retained in `results/memory-original/diabetes.log` (58,776 bytes,
91 blocks definitely lost; Valgrind exit 99). To reproduce that diagnosis:

```bash
python3 tools/memory.py --ref f19cc633664c9a333b208049770424d58d14909e --label memory-original-repeat --mode valgrind
```

This command is expected to fail the leak check; do not treat it as a passing
baseline. Memory diagnostics use `-O2 -g`, with additional instrumentation for
ASan/UBSan, and are not included in performance statistics. Sanitizer runs enable
leak detection and stop on errors. Final full-workload ASan/UBSan passed for all
three datasets, and final Diabetes Valgrind reported zero errors and zero bytes
in use at exit. Completed checks and output comparisons are recorded in
`results/task2-checks.json`. Logs are in `results/memory-final-asan`,
`results/memory-task2-asan` and `results/memory-task2-valgrind`.
Saved CSV charts cover all seven stages. Five-workload tables and charts also
include both image benchmarks.

### Image results

Silk waves baseline records are in `results/silk-baseline`: one warmup and three
measured runs, with unchanged formulas and quality across repeats. Measured
internal times were 426.405, 411.229 and 427.364 seconds (median 426.405 seconds).
To reproduce the original image search, use a new result label:

```bash
python3 tools/benchmark.py --label silk-baseline-repeat --datasets silk-wave
```

The completed optimized batch is in `results/silk-final-repeat`, using commit
`5132428` with explicit `-O2`. Its measured internal times were 38.846, 38.586 and
38.552 seconds (median 38.586 seconds), giving 11.05x median speedup over baseline.
Each version has one warmup and three measured runs; warmups are excluded.
All eight exported formulas and quality records match after timing removal.
RGB averaged test MSE is 0.0277195631 in both versions. All eight reconstructed
PNGs also have identical pixels and file hashes. The reconstructions differ
from the original input; optimization preserved the baseline quality.

Full-workload ASan/UBSan with leak detection passed in
`results/memory-silk-asan-repeat`. The first diagnostic attempt in
`results/memory-silk-asan` failed because LeakSanitizer could not operate under
restricted execution; both attempts are retained. Diagnostic and Racket render
times are excluded from performance statistics.
Checks and statistics: `results/silk-checks/checks.json` and
`results/silk-checks/summary.md`. Image comparison:
[PNG](results/silk-checks/comparison.png), [SVG](results/silk-checks/comparison.svg).

To repeat the optimized search and memory check, use new labels:

```bash
python3 tools/benchmark.py --ref 5132428 --label silk-final-new --datasets silk-wave '--flags=-std=c++17 -O2 -Wall -Wextra -I include -I.'
python3 tools/memory.py --ref 5132428 --label memory-silk-asan-new --mode sanitize --datasets silk-wave
racket results/silk-final-new/silk-wave-1.rkt results/silk-final-new/silk-wave-1.png
```

Square waves records are in `results/square-baseline` and `results/square-final`.
Each version has one warmup and three measured runs, using the same input,
seeds, 128 candidates, 16 generations and eight models per RGB channel.
The original commit and flags match the Silk baseline; the optimized version
uses `5132428` with `-O2`. Median internal time decreased from 1319.584 to
120.481 seconds (10.95x speedup); sample standard deviations were 25.382 and
0.146 seconds. All eight outputs match after timing removal, including formulas
and RGB averaged test MSE (0.0175210362). All eight reconstructed PNGs have
identical pixels and hashes. Full-workload ASan/UBSan with leak detection passed
in `results/memory-square-asan`; diagnostic and render times are excluded.

Checks and statistics: `results/square-checks/checks.json` and
`results/square-checks/summary.md`. Image comparison:
[PNG](results/square-checks/comparison.png), [SVG](results/square-checks/comparison.svg).
Reproduce with new labels:

```bash
python3 tools/benchmark.py --label square-baseline-new --datasets square-wave
python3 tools/benchmark.py --ref 5132428 --label square-final-new --datasets square-wave '--flags=-std=c++17 -O2 -Wall -Wextra -I include -I.'
python3 tools/memory.py --ref 5132428 --label memory-square-asan-new --mode sanitize --datasets square-wave
racket results/square-final-new/square-wave-1.rkt results/square-final-new/square-wave-1.png
```

### Single-run verification

For a single-run reproduction check, use fresh `verify-*` directories. This
runs all five workloads once per version, with no warmup. It does not replace
the repeated measurements used for the performance tables. These commands use
only committed source and preserve the current checkout:

```bash
mkdir results/verify-baseline results/verify-final
mkdir results/verify-baseline/source results/verify-final/source
git archive f19cc633664c9a333b208049770424d58d14909e | tar -x -C results/verify-baseline/source
git archive 5132428 | tar -x -C results/verify-final/source
make -C results/verify-baseline/source clean
make -C results/verify-baseline/source -j2 CXXFLAGS='-std=c++17 -Wall -Wextra -I include -I.'
make -C results/verify-final/source clean
make -C results/verify-final/source -j2 CXXFLAGS='-std=c++17 -O2 -Wall -Wextra -I include -I.'
(
  set -e
  cd results/verify-baseline/source
  for dataset in diabetes cancer housing silk-wave square-wave; do
    ./genetic_benchmark "$dataset" > "../$dataset.rkt" 2> "../$dataset.stderr"
  done
)
(
  set -e
  cd results/verify-final/source
  for dataset in diabetes cancer housing silk-wave square-wave; do
    ./genetic_benchmark "$dataset" > "../$dataset.rkt" 2> "../$dataset.stderr"
  done
)
racket results/verify-baseline/silk-wave.rkt results/verify-baseline/silk-wave.png
racket results/verify-final/silk-wave.rkt results/verify-final/silk-wave.png
racket results/verify-baseline/square-wave.rkt results/verify-baseline/square-wave.png
racket results/verify-final/square-wave.rkt results/verify-final/square-wave.png
```

The `.rkt` outputs contain time and quality records. Compare formulas and quality
with the saved results after removing `;;Time` lines; compare reconstructed PNG
pixels as well. Single-run checks are separate from performance statistics.
The original Square waves run takes about 22 minutes on the recorded VM.

### Verification results

Clean-checkout verification passed for code snapshot `f03db9b`: a fresh local
clone and new Python venv on the existing course VM. All five workloads ran
once per version without warmup. Formulas and quality records matched the saved
baseline, and all four reconstructed PNGs matched. The 17 Python tool tests,
five C++ sanitizer unit tests, default make build and saved-statistics/plot
regeneration passed. gprof and Valgrind smoke tests passed; perf remains blocked
by host permissions. Evidence: [summary](results/reproduce-check/summary.md),
[checks](results/reproduce-check/checks.json), and command/build/run logs in
`results/reproduce-check/`. Single-run times are excluded from the performance
tables. Full-workload memory checks were not repeated in this verification.

The standard venv command failed on this VM because ensurepip was unavailable;
the documented uv fallback worked. System tools were shared with the existing
VM; installation on a fresh OS was not tested. Temporary clone and venv were
removed after preserving the evidence. The primary experiment environment is
the course VM. Image baseline and optimized batches were measured separately
on the same VM rather than interleaved. Shared host activity can affect timings.

### Optional Docker

Docker is an optional setup. Its build and checks below passed.

Build and enter the tested container from the repository root:

```bash
./dockerbuild.sh cs598ape-mp2
./dockerrun.sh cs598ape-mp2
```

Inside the container, `/host` is the mounted repository. Run:

```bash
make clean
make -j2
./genetic_benchmark diabetes
exit
```

The image uses Ubuntu 24.04 and G++ 13.3.0 and includes the build, diagnostic,
Racket PNG and Python plotting dependencies. Container checks passed for eleven
Python tests, five C++ sanitizer tests, Diabetes execution and Valgrind, exported
Racket module loading, PNG rendering smoke tests and gprof. Diabetes formulas
and quality metrics matched the VM baseline. Records and image identifiers are
in `results/docker-check/checks.json`. Host permissions still block perf.
Container checks are separate from the VM performance measurements above.
Files created in `/host` remain in the repository with the current user's UID.
