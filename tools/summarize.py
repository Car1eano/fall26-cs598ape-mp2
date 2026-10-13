#!/usr/bin/env python3
"""Validate saved output and plot statistics from measured (not warmup) runs."""
import argparse
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
DATASETS = ['diabetes', 'cancer', 'housing']


def main():
    p = argparse.ArgumentParser()
    p.add_argument('labels', nargs='+')
    a = p.parse_args()
    runs = {label: json.loads((ROOT / 'results' / label / 'runs.json').read_text()) for label in a.labels}
    baseline = {d: next(r for r in runs[a.labels[0]] if r['dataset'] == d) for d in DATASETS}
    summary = []
    for label in a.labels:
        for dataset in DATASETS:
            all_rows = [r for r in runs[label] if r['dataset'] == dataset]
            rows = [r for r in all_rows if not r['warmup']]
            if len(rows) < 3:
                raise RuntimeError(f'{label}/{dataset}: need at least three measured runs')
            equivalent = all(r['returncode'] == 0 and r['output_sha256'] == baseline[dataset]['output_sha256'] for r in all_rows)
            entry = {'variant': label, 'dataset': dataset, 'n': len(rows), 'equivalent_output': equivalent,
                     'quality': rows[0]['quality']}
            for key in ['internal_seconds', 'wall_seconds']:
                values = [r[key] for r in rows]
                entry[key] = {'median': statistics.median(values), 'min': min(values), 'max': max(values),
                              'mean': statistics.mean(values), 'sample_stdev': statistics.stdev(values)}
            summary.append(entry)
    base_times = {r['dataset']: r['internal_seconds']['median'] for r in summary if r['variant'] == a.labels[0]}
    for r in summary:
        r['speedup'] = base_times[r['dataset']] / r['internal_seconds']['median']
    dest = ROOT / 'results'
    (dest / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    lines = ['# VM benchmark results', '', 'Warmup excluded. Three measured runs per dataset and variant.', '',
             '| Variant | Dataset | Internal median (s) | Min–max (s) | Wall median (s) | Speedup | Same output |',
             '|---|---|---:|---:|---:|---:|---|']
    for r in summary:
        t = r['internal_seconds']
        lines.append(f"| {r['variant']} | {r['dataset']} | {t['median']:.3f} | {t['min']:.3f}–{t['max']:.3f} | {r['wall_seconds']['median']:.3f} | {r['speedup']:.2f}x | {r['equivalent_output']} |")
    lines += ['', 'Full formulas, both candidates, stderr and build flags are saved in each variant directory.', '',
              '| Dataset | Candidate | Length | Depth | Raw fitness | Test quality |', '|---|---:|---:|---:|---:|---:|']
    for d in DATASETS:
        q = baseline[d]['quality']
        for i in range(2):
            vals = [line.split(': ', 1)[1] for line in q[i * 4:(i + 1) * 4]]
            lines.append(f"| {d} | {i + 1} | {' | '.join(vals)} |")
    (dest / 'summary.md').write_text('\n'.join(lines) + '\n')

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    for metric, filename, ylabel in [('internal_seconds', 'runtime.png', 'Internal end-to-end time (seconds; log scale)'),
                                    ('speedup', 'speedup.png', 'Speedup relative to baseline')]:
        fig, ax = plt.subplots(figsize=(10, 5), layout='constrained')
        width = 0.8 / len(a.labels)
        x = np.arange(len(DATASETS))
        for index, label in enumerate(a.labels):
            group = [next(r for r in summary if r['variant'] == label and r['dataset'] == d) for d in DATASETS]
            values = [r[metric]['median'] if isinstance(r[metric], dict) else r[metric] for r in group]
            errors = None
            if metric == 'internal_seconds':
                errors = [[r[metric]['median'] - r[metric]['min'] for r in group],
                          [r[metric]['max'] - r[metric]['median'] for r in group]]
            bars = ax.bar(x - 0.4 + width / 2 + index * width, values, width, label=label, yerr=errors, capsize=3)
            ax.bar_label(bars, fmt='%.2f', fontsize=8, padding=3)
        if metric == 'internal_seconds':
            ax.set_yscale('log')
        ax.set_xticks(x, ['Diabetes', 'Cancer', 'Housing'])
        ax.set_ylabel(ylabel)
        ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
        ax.set_title('Course VM: fixed datasets, seeds and training parameters (n=3)')
        ax.grid(axis='y', alpha=0.2)
        ax.set_axisbelow(True)
        fig.savefig(dest / filename, dpi=160)
        fig.savefig(dest / filename.replace('.png', '.svg'))
        plt.close(fig)
    print('\n'.join(lines))
    if not all(r['equivalent_output'] for r in summary):
        raise RuntimeError('Output differs from baseline; inspect summary before claiming equivalence')


if __name__ == '__main__':
    main()
