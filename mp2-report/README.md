# MP2 report

Authors: Carleano Chang and Christine Liou.

- `report.tex`: ACM SIGPLAN source using the `acmart` class.
- `report.pdf`: compiled report; three pages including references.
- `figures/stages.pdf` and `figures/overview.pdf`: figures sized for one column.
- `make_figures.py`: regenerate these figures from the existing result summaries.

## Build

From this folder, use a TeX installation with `acmart` and its dependencies:

```bash
latexmk -pdf report.tex
```

Alternatively, use Tectonic:

```bash
tectonic report.tex
```

The figures are included, and references are defined in `report.tex`.
No separate BibTeX file is needed. For Overleaf, upload `report.tex` and
`figures/` together and select `report.tex` as the main file.

## Figures and data

The report figures use the same measurements as the charts in `results/`, with
font sizes and dimensions adjusted for the paper. To regenerate them from the
repository root, use a Python environment with the shared plotting dependencies:

```bash
python -m pip install -r tools/plot-requirements.txt
python mp2-report/make_figures.py
```

The script reads [CSV results](../results/summary.json) and
[all five workloads](../results/all-summary.json) directly. It creates vector
PDFs and ignored PNG previews. No training or timing measurements are rerun.
Data copies, duplicate previews, previous drafts and build logs are omitted.

The report PDF is submitted separately on HotCRP.
