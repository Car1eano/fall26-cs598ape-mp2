# Silk waves verification

| Version | Median seconds | Min–max seconds | Sample stddev |
|---|---:|---:|---:|
| silk-baseline | 426.405 | 411.229–427.364 | 9.052 |
| silk-final-repeat | 38.586 | 38.552–38.846 | 0.161 |

Median speedup: 11.05x. One warmup and three measured runs per version.
Formulas, reported MSE and reconstructed pixels match. Full-workload ASan/UBSan passed.
Racket render times are recorded separately and excluded from search timings.
