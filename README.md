# 598APE-HW2

## MP2 performance experiments

This private artifact keeps the original workload and compares one change at a
time. The original commit is `f19cc633664c9a333b208049770424d58d14909e`.
The measured machine is the course VM `fa26-cs598a-048.cs.illinois.edu`, with
4 vCPUs (Intel Xeon Silver 4216), about 16 GiB RAM, Ubuntu 26.04.1 and G++ 15.2.0.
Full environment records are in [results/environment](results/environment).

Build, run and benchmark commands, changes and pending checks are listed below.
Saved statistics and charts: [results table](results/summary.md),
[runtime](results/runtime.png), [speedup](results/speedup.png).

| Change | Commit | Recorded experiment |
|---|---|---|
| Original baseline | `f19cc633664c9a333b208049770424d58d14909e` | `baseline` |
| Enable `-O2` | `e453776` | `o2` (same original source, explicit `-O2`) |
| Direct stack indexing | `cbc92ec` | `stack` (original flags), `o2-stack` (combined) |
| Stable index sorting | `a150e4f` | `sorted` |
| Free replaced hoist nodes | `4850ad7` | `hoist-fixed` |
| Fix integer range overflow | `5132428` | `final` |

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
```

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

Plotting requires Python with the packages in `tools/plot-requirements.txt`:

```bash
python3 -m venv /tmp/mp2-plots
/tmp/mp2-plots/bin/pip install -r tools/plot-requirements.txt
/tmp/mp2-plots/bin/python tools/summarize.py baseline o2 stack o2-stack sorted hoist-fixed final
```

If system Python lacks `venv`/`ensurepip`, install `python3-venv` or use
`uv venv /tmp/mp2-plots` and `uv pip install --python /tmp/mp2-plots/bin/python -r tools/plot-requirements.txt`.
The summary checks raw output hashes, recorded timings, repeat counts, dataset
hashes and baseline output with timing lines removed before writing tables or
standalone PNG/SVG charts. Invalid or inconsistent batches are rejected before
existing artifacts are changed.

For hotspot evidence and independent correctness checks:

```bash
perf stat -e task-clock true
python3 tools/profile.py --source results/baseline/source --label profile-repeat --optimization=-O0
python3 tools/check.py --source results/baseline/source --label check-repeat --optimization=-O0
python3 tools/check.py --source results/o2-stack/source --label check-sanitized-repeat --sanitize
python3 tools/check.py --source results/final/source --label check-final-repeat --sanitize --sorting --mutations --distributions
python3 tools/profile.py --source results/o2-stack/source --label profile-cancer-repeat --dataset cancer --optimization=-O2
python3 tools/profile.py --source results/sorted/source --label profile-sorted-repeat --dataset cancer --optimization=-O2
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
Saved charts cover the first four stages; later stages have raw records but have
not been added to those charts.

Silk waves baseline records are in `results/silk-baseline`: one warmup and three
measured runs, with unchanged formulas and quality across repeats. Measured
internal times were 426.405, 411.229 and 427.364 seconds (median 426.405 seconds).
To reproduce the original image search, use a new result label:

```bash
python3 tools/benchmark.py --label silk-baseline-repeat --datasets silk-wave
```

The optimized Silk waves batch is incomplete and is not included in these
results. Image memory checks and reconstructed PNG comparisons are pending.
Square waves has not been measured. Clean-environment reproduction is pending;
the primary experiment environment is the course VM.

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

Original README follows, including the supplied image examples.

This repository contains code for homework 2 of 598APE.

In particular, this repository is an implementation of Symbolic Regression and the various contexts it can be used in.

To compile the program run:
```bash
make -j
```

To clean existing build artifacts run:
```bash
make clean
```

This program assumes the following are installed on your machine:
* A working C++ compiler (g++ is assumed in the Makefile)
* make
* racket (to plot images)

Running make builds a sample benchmarking binary(`genetic_benchmark`) which you will use for perf engineering. However, note that the symbolic regression routines exposed in `genetic.h` are general, and can be used as a sub-routine in any data science pipeline (pending a Cython wrapper to Python/Torch).

Once compiled, one can run the benchmark code on the diabetes dataset as follows. The output is a valid racket program, which provides the 2 best programs as callable functions - symbolic regression is used for synthesizing these functions. 

```bash
./genetic_benchmark diabetes
#lang racket

;;===== Symbolic Regression Benchmark =====

(provide best-program-1 best-program-2)
;;Loading dataset...
;;Dataset dimensions: 442 samples x 10 features
;;Training symbolic regressor with 512 population size and 16 generations
;;Best program 1 details:
;;- Length: 91 nodes
;;- Depth: 12
;;- Raw fitness: 6302.75
;;- Test MSE: 7468.95
(define best-program-1 (lambda (X)
  (define (div a b) (if (< (abs b) 0.001) 1.0 (/ a b)))
  (define (fdim a b) (max (- a b) 0.0))
  (define (gt a b) (if (> a b) 1.0 0.0))
  (define (acosh a)
    (log (+ a (* (sqrt (- a 1.0)) (sqrt (+ a 1.0))))))
  (define (asinh a)
    (let* ([v (abs a)] [r (log (+ v (sqrt (+ (* v v) 1.0))))])
      (if (< a 0.0) (- r) r)))
  (define (atanh a) (* 0.5 (log (/ (+ 1.0 a) (- 1.0 a)))))
  (define (cbrt a)
    (let ([r (expt (abs a) (/ 1.0 3.0))])
      (if (< a 0.0) (- r) r)))
  (define (cube a) (* a a a))
  (define (inv a) (if (< (abs a) 0.001) 0.0 (/ 1.0 a)))
  (define (rcbrt a) (/ 1.0 (cbrt a)))
  (define (rsqrt a) (/ 1.0 (sqrt (abs a))))
  (define (gp-log a) (if (< (abs a) 0.001) 0.0 (log (abs a))))
  (define (gp-sqrt a) (sqrt (abs a)))
  (*  (-  (-  (+  (cos  (+  (cos  (-  (gp-log  (-  (list-ref X 0) (abs  (list-ref X 8)) ) )  (-  (-  (list-ref X 1) (list-ref X 8))  (sin  (list-ref X 7)) ) ) )  (sin  (cos  (cos  (*  (sin  (cos  (list-ref X 8)) )  (gp-log  (-  (list-ref X 6) (list-ref X 5)) ) ) ) ) ) ) )  (cos  (*  (list-ref X 7) (list-ref X 7)) ) )  (*  (sin  (cos  (list-ref X 8)) )  (gp-log  (-  (list-ref X 6) (list-ref X 5)) ) ) )  (-  (-  (cos  (fdim  (list-ref X 2) (list-ref X 9)) )  (-  (cos  (fdim  (list-ref X 8) (list-ref X 6)) )  (gp-log  (list-ref X 0)) ) )  (*  -0.960798442 (list-ref X 5)) ) )  (+  (fdim  (-  (sin  (cos  (+  (list-ref X 5) (list-ref X 0)) ) )  (cos  (cos  (list-ref X 4)) ) )  (+  (gp-log  (list-ref X 1))  (cos  (gp-log  (list-ref X 9)) ) ) )  (+  (-  (fdim  (abs  (list-ref X 3))  (gp-log  (*  (list-ref X 1) (list-ref X 1)) ) )  (gp-log  (*  (list-ref X 1) (list-ref X 1)) ) )  (abs  (cos  (list-ref X 6)) ) ) ) ) ))
;;Best program 2 details:
;;- Length: 199 nodes
;;- Depth: 18
;;- Raw fitness: 6408.27
;;- Test MSE: 7217.17
(define best-program-2 (lambda (X)
  (define (div a b) (if (< (abs b) 0.001) 1.0 (/ a b)))
  (define (fdim a b) (max (- a b) 0.0))
  (define (gt a b) (if (> a b) 1.0 0.0))
  (define (acosh a)
    (log (+ a (* (sqrt (- a 1.0)) (sqrt (+ a 1.0))))))
  (define (asinh a)
    (let* ([v (abs a)] [r (log (+ v (sqrt (+ (* v v) 1.0))))])
      (if (< a 0.0) (- r) r)))
  (define (atanh a) (* 0.5 (log (/ (+ 1.0 a) (- 1.0 a)))))
  (define (cbrt a)
    (let ([r (expt (abs a) (/ 1.0 3.0))])
      (if (< a 0.0) (- r) r)))
  (define (cube a) (* a a a))
  (define (inv a) (if (< (abs a) 0.001) 0.0 (/ 1.0 a)))
  (define (rcbrt a) (/ 1.0 (cbrt a)))
  (define (rsqrt a) (/ 1.0 (sqrt (abs a))))
  (define (gp-log a) (if (< (abs a) 0.001) 0.0 (log (abs a))))
  (define (gp-sqrt a) (sqrt (abs a)))
  (*  (-  (-  (+  (cos  (*  (list-ref X 7) (list-ref X 7)) )  (cos  (*  (list-ref X 7) (list-ref X 7)) ) )  (*  (sin  (cos  (list-ref X 8)) )  (gp-log  (-  (list-ref X 6) (list-ref X 5)) ) ) )  (-  (-  (gp-log  (list-ref X 6))  (-  (sin  (list-ref X 5))  (gp-log  (list-ref X 0)) ) )  (sin  (sin  (+  (-  (-  (-  (+  (+  (cos  (list-ref X 6))  (fdim  (list-ref X 4) (list-ref X 0)) )  (abs  (gp-log  (list-ref X 3)) ) )  (*  (gp-log  (+  (list-ref X 4) (list-ref X 8)) )  (cos  (sin  (fdim  (-  (list-ref X 0) (list-ref X 9))  (abs  (list-ref X 8)) ) ) ) ) )  (-  (-  (cos  (fdim  (list-ref X 2) (list-ref X 9)) )  (-  (*  (gp-log  (*  (*  (abs  (-  (abs  (list-ref X 8))  (+  (list-ref X 5) (list-ref X 5)) ) )  (sin  (list-ref X 1)) )  (cos  (sin  (list-ref X 1)) ) ) )  (-  (+  (cos  (cos  (list-ref X 0)) )  (+  (fdim  (list-ref X 2) (list-ref X 9))  (abs  (list-ref X 1)) ) )  (cos  (cos  (gp-log  (abs  (-  (list-ref X 5) (list-ref X 7)) ) ) ) ) ) )  (-  (sin  (list-ref X 5))  (gp-log  (list-ref X 0)) ) ) )  (abs  (+  (list-ref X 2) (list-ref X 9)) ) ) )  (abs  (-  (list-ref X 6) (gp-log  (list-ref X 7)) ) ) )  (list-ref X 9)) ) ) ) )  (+  (fdim  (-  (sin  (-  (-  (+  (cos  (+  (cos  (-  (gp-log  (-  (list-ref X 0) (abs  (list-ref X 8)) ) )  (-  (-  (list-ref X 1) (list-ref X 8))  (sin  (list-ref X 7)) ) ) )  (sin  (cos  (cos  (sin  (list-ref X 5)) ) ) ) ) )  (cos  (*  (list-ref X 7) (list-ref X 7)) ) )  (*  (sin  (cos  (list-ref X 8)) )  (gp-log  (-  (list-ref X 6) (list-ref X 5)) ) ) )  (-  (-  (cos  (fdim  (list-ref X 2) (list-ref X 9)) )  (-  (cos  (fdim  (list-ref X 8) (list-ref X 6)) )  (gp-log  (list-ref X 0)) ) )  (*  -0.960798442 (list-ref X 5)) ) ) )  (cos  (+  (+  (cos  (list-ref X 6))  (list-ref X 9))  (abs  (gp-log  (list-ref X 3)) ) ) ) )  (+  (gp-log  (list-ref X 1))  (cos  (gp-log  (list-ref X 9)) ) ) )  (fdim  (+  (+  (cos  (list-ref X 6))  (*  (list-ref X 7) (list-ref X 7)) )  (abs  (gp-log  (list-ref X 3)) ) )  (gp-log  (-  (list-ref X 6) (list-ref X 5)) ) ) ) ) ))
;;Time(Symbolic Regression (End-to-End)) = 11.512300000 sec

```

`(list-ref X i)` corresponds to the `i`th feature of your dataset (it is Racket syntax to access `X[i]`)

While currently hardcoded to only handle the 3 CSV datasets and 2 image reconstruction tasks, `genetic_benchmark.cpp` in the `benchmarks` folder exposes training code for end to end symbolic regression/binary classification, starting from converting the input data to a columnar format, before dispatching it to `genetic::symFit`. 

The behaviour of the training run can be tuned through the `param` struct, which controls paramenters like the population size, functions being considered, subtree depth and so on.  

```bash
./genetic_benchmark diabetes
```

There are also 2 image reconstruction tasks. The goal of image re-construction is to infer the underlying semantic meaning present in an image. We do this by representing every image as the average of `K` mathematical equations, and output the equations as a valid racket program (which you can also use to draw the final image). All input images have 256x256 pixels, and each pixel stores a r,g,b tuple corresponding to red, green and blue pixel values. For example, on the silk-wave input:

![Silk wave](./benchmark/silk-waves.png)

We now run symbolic regression based reconstruction on the silk-wave picture. 

```bash
./genetic_benchmark silk-wave > silk-ref.rkt
racket silk-ref.rkt silk-waves-reconstructed.png
```

This produces 2 artifacts. [silk-ref.rkt](./benchmark/silk-ref.rkt) contains the symbolic definition of the image. The reconstructed image is 

![Reconstructed Silk wave](./benchmark/silk-waves-reconstructed.png)

Similarly, for the harder square wave benchmark, we start from 

![Square wave](./benchmark/squared-waves.png)

and are able to reconstruct 

![Reconstructed square wave](./benchmark/square-wave-reconstructed.png)

with the source code for the reconstructed wave in [square-wave-ref.rkt](./benchmark/square-wave-ref.rkt)

The time taken for the end to end run can be seen in the last comment of the generated rkt file. Similar to HW1, your goal is to reduce this runtime as much as possible, while maintining/increasing complexity. For the image code, it is sufficient to just optimize image generation, however, you are also free to optimize image drawing too (which is currently implemnented as a DSL in Racket)

## Input Datasets and Images
This project contains 3 input datasets and 2 images for you to optimize. All 3 are standard scikit-learn datasets. The images are generated bitmaps from `benchmark/generate-easy-image.rkt`.

### Diabetes

```bash
./genetic_benchmark diabetes
```

### Cancer

```bash
./genetic_benchmark cancer
```

### California Housing Prices

```bash
./genetic_benchmark housing
```

### Silk waves

```bash
./genetic_benchmark silk-wave > silk.rkt
racket silk.rkt silk.png
```

### Square waves

```bash
./genetic_benchmark square-wave > square.rkt
racket square.rkt square.png
```

## Code Overview

There are multiple core functions

`cpp_evolve`

`cpp_evolve` is the central evolution driver. It takes a population of candidate programs and produces a new generation by first selecting parents through tournament selection and then applying various mutation strategies (crossover, subtree mutation, hoist mutation, and point mutation) or direct reproduction. After mutation, it updates the fitness of the new generation.

`build_program`

`build_program` constructs an initial candidate program (represented as a syntax tree) using a randomized process. It chooses function nodes and terminal nodes based on specified initialization methods (grow, full, or half-and-half) and ensures that the generated program adheres to a maximum depth constraint.

`tournament_kernel` 

`tournament_kernel` implements the tournament selection process. It randomly samples subsets of the population, evaluates their fitness (including a parsimony penalty for program length), and selects the best candidates to serve as parents for the next generation.

`execute_kernel`

Given a bunch of programs(symbolic formulae), `execute_kernel` evaluates those formulae on the given input dataset and outputs predicted values. We evaluate all programs on all dataset rows. 

`compute_metric`

As the name suggests, we compute the loss/accuracy values according to the metric specified in `params`. There are 5 different metrics supported - logLoss (for classification), mean square error and root mean square error(for regression) and correlation coefficients for transformation (both Karl Pearson and Spearman's rank correlation are implemented). 

## Docker

For ease of use and installation, we provide a docker image capable of running and building code here. The source docker file is in /docker (which is essentially a list of commands to build an OS state from scratch). It contains the dependent compilers, and some other nice things.

Run the docker build for the first time to setup all the environments you need
```bash
./dockerbuild.sh
```

If you now run `./dockerrun.sh` you will enter an interactive bash session with all the packages from docker installed (that script by default uses `vim/598ape`, feel free to replace it with whatever location you like if you built from scratch). The current directory (aka this folder) is mounted within `/host`. Any files you create on your personal machine will be available there, and anything you make in the container in that folder will be available on your personal machine.
