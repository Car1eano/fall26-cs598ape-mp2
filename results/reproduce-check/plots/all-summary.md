# Five-workload VM results

Median of measured internal times; warmups excluded; measured repeats per group: [3].

| Workload | Baseline median (s) | Final median (s) | Speedup | Baseline min–max (s) | Final min–max (s) | Baseline / final sample stddev (s) |
|---|---:|---:|---:|---:|---:|---:|
| Diabetes | 21.220 | 1.684 | 12.60x | 21.211–21.650 | 1.683–1.687 | 0.251 / 0.002 |
| Cancer | 130.977 | 13.449 | 9.74x | 130.798–132.965 | 13.420–13.711 | 1.203 / 0.160 |
| Housing | 248.850 | 24.809 | 10.03x | 247.147–252.221 | 24.795–24.872 | 2.582 / 0.041 |
| Silk waves | 426.405 | 38.586 | 11.05x | 411.229–427.364 | 38.552–38.846 | 9.052 / 0.161 |
| Square waves | 1319.584 | 120.481 | 10.95x | 1275.788–1319.917 | 120.273–120.554 | 25.382 / 0.146 |

Formulas and quality match baseline in all five workloads. Both image reconstructions have identical PNG hashes across versions.

Shared VM; batches not interleaved; image stages are baseline and combined final only. Rendering and diagnostic times excluded.

CSV stage details: [summary.md](summary.md).
Image quality records: [Silk](silk-checks/checks.json), [Square](square-checks/checks.json).

Each image run trains the original model count: Silk 9 models, Square 24 models. No intermediate image stages were measured.
