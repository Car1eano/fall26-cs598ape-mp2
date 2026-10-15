#!/usr/bin/env python3
"""Validate saved output and plot statistics from measured (not warmup) runs."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import statistics

ROOT = Path(__file__).resolve().parents[1]
DATASETS = ['diabetes', 'cancer', 'housing']


def load_runs(directory, datasets=None):
    datasets = DATASETS if datasets is None else datasets
    metadata = json.loads((directory / 'metadata.json').read_text())
    repeats = metadata['repeats']
    if type(repeats) is not int or repeats < 3 or metadata['warmups'] != 1:
        raise ValueError(f'{directory.name}: need one warmup and at least three repeats')
    if sorted(metadata['datasets']) != sorted(datasets):
        raise ValueError(f'{directory.name}: unexpected dataset list')
    if '-pg' in metadata['flags'].split() or '-fsanitize=' in metadata['flags']:
        raise ValueError(f'{directory.name}: instrumented runs are not performance measurements')
    rows = json.loads((directory / 'runs.json').read_text())
    if len(rows) != len(datasets) * (repeats + 1):
        raise ValueError(f'{directory.name}: incomplete or extra run records')
    for dataset in datasets:
        group = [r for r in rows if r['dataset'] == dataset]
        if sorted(r['run'] for r in group) != list(range(repeats + 1)):
            raise ValueError(f'{directory.name}/{dataset}: missing or duplicate run IDs')
        for row in group:
            if row['warmup'] != (row['run'] == 0) or row['returncode'] != 0:
                raise ValueError(f'{directory.name}/{dataset}: failed run or invalid warmup flag')
            stem = dataset + '-' + ('warmup' if row['run'] == 0 else str(row['run']))
            output = (directory / (stem + '.rkt')).read_text()
            normalized = ''.join(line for line in output.splitlines(keepends=True)
                                 if not line.startswith(';;Time'))
            digest = hashlib.sha256(normalized.encode()).hexdigest()
            if digest != row['output_sha256']:
                raise ValueError(f'{directory.name}/{stem}: raw output hash mismatch')
            timing = re.search(r';;Time\([^\n]+\) = ([0-9.]+) sec', output)
            if not timing or float(timing[1]) != row['internal_seconds']:
                raise ValueError(f'{directory.name}/{stem}: raw timing mismatch')
            for key in ['internal_seconds', 'wall_seconds']:
                if not math.isfinite(row[key]) or row[key] <= 0:
                    raise ValueError(f'{directory.name}/{stem}: invalid {key}')
            if row['wall_seconds'] < row['internal_seconds']:
                raise ValueError(f'{directory.name}/{stem}: wall time precedes internal time')
            quality = [line for line in output.splitlines() if line.startswith(';;-')]
            expected_count = 8 if dataset in DATASETS else 0
            if quality != row['quality'] or len(quality) != expected_count:
                raise ValueError(f'{directory.name}/{stem}: quality record mismatch')
            row['_stderr'] = (directory / (stem + '.stderr')).read_text()
        warmup = next(r for r in group if r['run'] == 0)
        if not all(r['output_sha256'] == warmup['output_sha256'] and
                   r['_stderr'] == warmup['_stderr'] and r['matches_warmup'] for r in group):
            raise ValueError(f'{directory.name}/{dataset}: inconsistent repeated outputs')
    return metadata, rows


def build_summary(labels, results_dir):
    if not labels or len(set(labels)) != len(labels):
        raise ValueError('Use a nonempty list of unique experiment labels')
    loaded = {label: load_runs(results_dir / label) for label in labels}
    baseline_meta, baseline_rows = loaded[labels[0]]
    baseline = {d: next(r for r in baseline_rows if r['dataset'] == d) for d in DATASETS}
    summary = []
    for label in labels:
        metadata, runs = loaded[label]
        for dataset in DATASETS:
            data_file = 'benchmark/' + dataset + '.csv'
            if metadata['source_files'][data_file] != baseline_meta['source_files'][data_file]:
                raise ValueError(f'{label}/{dataset}: dataset hash differs from baseline')
            all_rows = [r for r in runs if r['dataset'] == dataset]
            if not all(r['output_sha256'] == baseline[dataset]['output_sha256'] and
                       r['_stderr'] == baseline[dataset]['_stderr'] for r in all_rows):
                raise ValueError(f'{label}/{dataset}: output differs from baseline')
            rows = [r for r in all_rows if not r['warmup']]
            entry = {'variant': label, 'dataset': dataset, 'n': len(rows),
                     'equivalent_output': True, 'quality': rows[0]['quality']}
            for key in ['internal_seconds', 'wall_seconds']:
                values = [r[key] for r in rows]
                entry[key] = {'median': statistics.median(values), 'min': min(values), 'max': max(values),
                              'mean': statistics.mean(values), 'sample_stdev': statistics.stdev(values)}
            summary.append(entry)
    base_times = {r['dataset']: r['internal_seconds']['median'] for r in summary if r['variant'] == labels[0]}
    for row in summary:
        row['speedup'] = base_times[row['dataset']] / row['internal_seconds']['median']
    return summary, baseline


def main():
    p = argparse.ArgumentParser()
    p.add_argument('labels', nargs='+')
    a = p.parse_args()
    dest = ROOT / 'results'
    summary, baseline = build_summary(a.labels, dest)
    (dest / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    counts = sorted({r['n'] for r in summary})
    repeat_note = f'Measured repeats per group: {counts}. Warmup excluded.'
    lines = ['# VM benchmark results', '', repeat_note, '',
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
        fig, ax = plt.subplots(figsize=(13, 5.5), layout='constrained')
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
            ax.bar_label(bars, fmt='%.2f', fontsize=7, padding=3, rotation=90)
        if metric == 'internal_seconds':
            ax.set_yscale('log')
        ax.set_xticks(x, ['Diabetes', 'Cancer', 'Housing'])
        ax.set_ylabel(ylabel)
        ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
        ax.set_title('Course VM: fixed datasets, seeds and training parameters (' +
                     ('n=' + str(counts[0]) if len(counts) == 1 else 'repeat counts vary') + ')')
        ax.grid(axis='y', alpha=0.2)
        ax.set_axisbelow(True)
        ax.margins(y=0.22)
        fig.savefig(dest / filename, dpi=160)
        fig.savefig(dest / filename.replace('.png', '.svg'))
        plt.close(fig)
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
