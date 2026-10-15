# Square waves verification

| Version | Median seconds | Min–max seconds | Sample stddev |
|---|---:|---:|---:|
| square-baseline | 1319.584 | 1275.788–1319.917 | 25.382 |
| square-final | 120.481 | 120.273–120.554 | 0.146 |

Median speedup: 10.95x. One warmup and three measured runs per version.
Formulas, reported MSE and reconstructed pixels match. Full-workload ASan/UBSan passed.
Racket render times are recorded separately and excluded from search timings.
