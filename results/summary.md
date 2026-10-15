# VM benchmark results

Measured repeats per group: [3]. Warmup excluded.

| Variant | Dataset | Internal median (s) | Min–max (s) | Wall median (s) | Speedup | Same output |
|---|---|---:|---:|---:|---:|---|
| baseline | diabetes | 21.220 | 21.211–21.650 | 21.225 | 1.00x | True |
| baseline | cancer | 130.977 | 130.798–132.965 | 131.003 | 1.00x | True |
| baseline | housing | 248.850 | 247.147–252.221 | 248.859 | 1.00x | True |
| o2 | diabetes | 10.170 | 10.137–10.204 | 10.174 | 2.09x | True |
| o2 | cancer | 60.702 | 60.429–60.860 | 60.726 | 2.16x | True |
| o2 | housing | 117.940 | 117.707–118.115 | 117.947 | 2.11x | True |
| stack | diabetes | 8.518 | 8.509–8.531 | 8.522 | 2.49x | True |
| stack | cancer | 71.252 | 71.187–71.267 | 71.278 | 1.84x | True |
| stack | housing | 112.376 | 112.375–112.415 | 112.385 | 2.21x | True |
| o2-stack | diabetes | 1.717 | 1.712–1.761 | 1.721 | 12.36x | True |
| o2-stack | cancer | 18.293 | 18.279–18.339 | 18.318 | 7.16x | True |
| o2-stack | housing | 24.913 | 24.712–25.062 | 24.919 | 9.99x | True |
| sorted | diabetes | 1.692 | 1.680–1.705 | 1.696 | 12.54x | True |
| sorted | cancer | 13.292 | 13.279–13.572 | 13.315 | 9.85x | True |
| sorted | housing | 24.744 | 24.655–24.753 | 24.750 | 10.06x | True |
| hoist-fixed | diabetes | 1.703 | 1.700–1.716 | 1.708 | 12.46x | True |
| hoist-fixed | cancer | 13.440 | 13.425–13.456 | 13.462 | 9.75x | True |
| hoist-fixed | housing | 24.844 | 24.800–24.854 | 24.850 | 10.02x | True |
| final | diabetes | 1.684 | 1.683–1.687 | 1.688 | 12.60x | True |
| final | cancer | 13.449 | 13.420–13.711 | 13.472 | 9.74x | True |
| final | housing | 24.809 | 24.795–24.872 | 24.815 | 10.03x | True |

Full formulas, both candidates, stderr and build flags are saved in each variant directory.

| Dataset | Candidate | Length | Depth | Raw fitness | Test quality |
|---|---:|---:|---:|---:|---:|
| diabetes | 1 | 91 nodes | 12 | 6302.75 | 7468.95 |
| diabetes | 2 | 199 nodes | 18 | 6408.27 | 7217.17 |
| cancer | 1 | 20 nodes | 5 | 0.15991 | 0.946903 |
| cancer | 2 | 20 nodes | 5 | 0.15991 | 0.946903 |
| housing | 1 | 28 nodes | 7 | 0.659991 | 0.64586 |
| housing | 2 | 23 nodes | 5 | 0.754433 | 0.728984 |
