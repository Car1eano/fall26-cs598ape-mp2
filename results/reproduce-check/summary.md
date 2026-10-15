# Clean-checkout verification

Code snapshot: `f03db9bc0a12826b61a97675fe6491e65188646e`.

Clean local clone and a new Python venv on the existing course VM. System packages were shared; fresh-OS installation was not tested.

One execution per workload and version; no warmup. These results are reproduction checks and are excluded from the report performance statistics.

| Workload | Baseline seconds | Final seconds | Single-run speedup | Output matches |
|---|---:|---:|---:|---|
| diabetes | 21.544 | 1.709 | 12.61x | Yes |
| cancer | 131.039 | 13.492 | 9.71x | Yes |
| housing | 252.222 | 24.887 | 10.13x | Yes |
| silk-wave | 409.931 | 38.127 | 10.75x | Yes |
| square-wave | 1319.555 | 120.246 | 10.97x | Yes |

All formulas and quality records match the saved baseline. All four reconstructed PNGs match the saved PNG hashes.

17 Python tool tests and five C++ sanitizer unit tests passed. Default make produced the same binary as the explicit final flags. Saved statistics regenerated identically; eight PNG/SVG chart files were regenerated.

gprof and Valgrind smoke tests passed. perf remains blocked by host permissions (perf_event_paranoid=4). Full-workload memory results remain in the earlier experiment records; they were not rerun here.

Standard venv creation failed because ensurepip was unavailable; the documented uv fallback succeeded. README source-directory references were corrected and single-run commands were added.

Commands and logs are retained in this directory. Temporary clone and venv were removed after preserving evidence.
