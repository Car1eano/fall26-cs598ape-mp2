#!/usr/bin/env python3
"""Check saved CSV/image evidence and regenerate the complete VM result set."""
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import sys

import summarize

ROOT = Path(__file__).resolve().parents[1]
LABELS = ['baseline', 'o2', 'stack', 'o2-stack', 'sorted', 'hoist-fixed', 'final']
IMAGES = [('silk', 'silk-final-repeat', 'silk-waves.png'),
          ('square', 'square-final', 'squared-waves.png')]
BASE = 'f19cc633664c9a333b208049770424d58d14909e'
FINAL = '51324285ab91bd7b27998be74809728a1ce7c23e'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def entry(label, dataset, rows, quality):
    measured = [r for r in rows if not r['warmup']]
    result = {'variant': label, 'dataset': dataset, 'n': len(measured),
              'equivalent_output': True, 'quality': quality}
    for key in ['internal_seconds', 'wall_seconds']:
        values = [r[key] for r in measured]
        result[key] = {'median': statistics.median(values), 'min': min(values),
                       'max': max(values), 'mean': statistics.mean(values),
                       'sample_stdev': statistics.stdev(values)}
    return result


def image_pair(kind, final_label, filename, root):
    dataset = kind + '-wave'
    results = root / 'results'
    evidence = json.loads((results / (kind + '-checks/checks.json')).read_text())
    require(all(evidence.get(k) is True for k in ['complete', 'formula_and_quality_identical',
            'rendered_pixels_identical', 'full_workload_asan_ubsan_passed']), 'Incomplete image checks')
    baseline_digest = None
    png_hashes = set()
    pair = []
    for label, commit in [(kind + '-baseline', BASE), (final_label, FINAL)]:
        folder = results / label
        meta, rows = summarize.load_runs(folder, [dataset])
        require(meta['commit'] == commit and not meta['stack_candidate'], 'Unexpected image source')
        flags = '-std=c++17 ' + ('-O2 ' if commit == FINAL else '') + '-Wall -Wextra -I include -I.'
        require(meta['flags'] == flags, 'Unexpected image compiler flags')
        require(meta['source_files']['benchmark/' + filename] == sha(root / 'benchmark' / filename),
                'Image input hash mismatch')
        quality = None
        if baseline_digest is None:
            baseline_digest = rows[0]['output_sha256']
        for row in rows:
            require(row['output_sha256'] == baseline_digest and not row['_stderr'],
                    'Image formulas or stderr differ')
            stem = dataset + '-' + ('warmup' if row['warmup'] else str(row['run']))
            output = (folder / (stem + '.rkt')).read_text()
            lines = [l for l in output.splitlines() if l.startswith(';;') and 'MSE' in l]
            require(lines == evidence['stages'][label]['quality_lines'], 'Image quality record mismatch')
            require(len(lines) == (13 if kind == 'silk' else 28), 'Incomplete model quality output')
            quality = lines
            png_hash = sha(folder / (stem + '.png'))
            saved = next(p for p in evidence['stages'][label]['rendered'] if p['run'] == row['run'])
            require(png_hash == saved['png_sha256'], 'Reconstructed PNG hash mismatch')
            png_hashes.add(png_hash)
        computed = entry(label, dataset, rows, quality)
        for old_key, new_key in [('median_seconds', 'median'), ('min_seconds', 'min'),
                                  ('max_seconds', 'max'), ('mean_seconds', 'mean'),
                                  ('sample_stddev_seconds', 'sample_stdev')]:
            require(evidence['stages'][label][old_key] == computed['internal_seconds'][new_key],
                    'Saved image statistics differ from raw runs')
        pair.append(computed)
    require(len(png_hashes) == 1, 'Image PNGs differ across versions')
    diagnostic = root / evidence['diagnostic_results']
    require(json.loads((diagnostic / 'checks.json').read_text()) == [
        {'dataset': dataset, 'command': ['./genetic_benchmark', dataset], 'returncode': 0}],
        'Image diagnostic failed')
    meta = json.loads((diagnostic / 'metadata.json').read_text())
    require(meta['commit'] == FINAL and meta['mode'] == 'sanitize' and
            '-fsanitize=address,undefined' in meta['flags'] and
            meta['environment']['ASAN_OPTIONS'] == 'detect_leaks=1:halt_on_error=1' and
            meta['environment']['UBSAN_OPTIONS'] == 'halt_on_error=1:print_stacktrace=1',
            'Image diagnostic flags differ')
    require(not (diagnostic / (dataset + '.log')).read_bytes(), 'Image diagnostic has errors')
    text = (diagnostic / (dataset + '.rkt')).read_text()
    normalized = ''.join(l for l in text.splitlines(keepends=True) if not l.startswith(';;Time'))
    require(hashlib.sha256(normalized.encode()).hexdigest() == baseline_digest,
            'Image diagnostic output differs')
    return pair


def build_all(root):
    results = root / 'results'
    csv, _ = summarize.build_summary(LABELS, results)
    meta = json.loads((results / 'baseline/metadata.json').read_text())
    for dataset in summarize.DATASETS:
        key = 'benchmark/' + dataset + '.csv'
        require(meta['source_files'][key] == sha(root / key), 'CSV input hash mismatch')
    workloads = []
    for dataset, title in zip(summarize.DATASETS, ['Diabetes', 'Cancer', 'Housing']):
        workloads.append({'dataset': dataset, 'title': title, 'kind': 'CSV',
                          'baseline': next(r for r in csv if r['dataset'] == dataset and r['variant'] == 'baseline'),
                          'final': next(r for r in csv if r['dataset'] == dataset and r['variant'] == 'final')})
    for kind, final_label, filename in IMAGES:
        baseline, final = image_pair(kind, final_label, filename, root)
        workloads.append({'dataset': kind + '-wave', 'title': kind.title() + ' waves',
                          'kind': 'Image', 'baseline': baseline, 'final': final})
    for item in workloads:
        item['speedup'] = item['baseline']['internal_seconds']['median'] / item['final']['internal_seconds']['median']
    groups = csv + [w[k] for w in workloads if w['kind'] == 'Image' for k in ['baseline', 'final']]
    measured = sum(g['n'] for g in groups)
    counts = sorted({g['n'] for g in groups})
    return {'complete': True, 'workloads': workloads, 'csv_stages': LABELS,
            'total_runs': measured + len(groups), 'measured_runs': measured,
            'warmup_runs': len(groups), 'repeat_counts': counts,
            'statistic': f'Median of measured internal times; warmups excluded; measured repeats per group: {counts}',
            'limitations': 'Shared VM; batches not interleaved; image stages are baseline and combined final only. Rendering and diagnostic times excluded.'}


def write_overview(result, dest):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np

    items = result['workloads']
    lines = ['# Five-workload VM results', '', result['statistic'] + '.', '',
             '| Workload | Baseline median (s) | Final median (s) | Speedup | Baseline min–max (s) | Final min–max (s) | Baseline / final sample stddev (s) |',
             '|---|---:|---:|---:|---:|---:|---:|']
    for w in items:
        b, f = [w[k]['internal_seconds'] for k in ['baseline', 'final']]
        lines.append(f"| {w['title']} | {b['median']:.3f} | {f['median']:.3f} | {w['speedup']:.2f}x | {b['min']:.3f}–{b['max']:.3f} | {f['min']:.3f}–{f['max']:.3f} | {b['sample_stdev']:.3f} / {f['sample_stdev']:.3f} |")
    lines += ['', 'Formulas and quality match baseline in all five workloads. Both image reconstructions have identical PNG hashes across versions.', '',
              result['limitations'], '', 'CSV stage details: [summary.md](summary.md).',
              'Image quality records: [Silk](silk-checks/checks.json), [Square](square-checks/checks.json).',
              '', 'Each image run trains the original model count: Silk 9 models, Square 24 models. No intermediate image stages were measured.']
    (dest / 'all-summary.json').write_text(json.dumps(result, indent=2) + '\n')
    (dest / 'all-summary.md').write_text('\n'.join(lines) + '\n')

    y = np.arange(len(items))
    fig, ax = plt.subplots(figsize=(10, 5), layout='constrained')
    for key, offset, color, label in [('baseline', -0.18, '#4477aa', 'Baseline'),
                                       ('final', 0.18, '#228833', 'Final')]:
        stats = [w[key]['internal_seconds'] for w in items]
        values = [s['median'] for s in stats]
        errors = [[s['median'] - s['min'] for s in stats],
                  [s['max'] - s['median'] for s in stats]]
        bars = ax.barh(y + offset, values, height=0.32, xerr=errors, capsize=3, color=color, label=label)
        ax.bar_label(bars, fmt='%.2f s', padding=6, fontsize=9)
    ax.set_xscale('log')
    ax.set_xlim(right=max(w['baseline']['internal_seconds']['max'] for w in items) * 2.4)
    ax.set_yticks(y, [w['title'] for w in items]); ax.invert_yaxis()
    ax.set_xlabel('Internal end-to-end time (seconds; log scale)')
    repeat_label = 'n=' + str(result['repeat_counts'][0]) if len(result['repeat_counts']) == 1 else 'repeat counts vary'
    ax.set_title(f'Five workloads: median and observed min–max ({repeat_label})')
    ax.grid(axis='x', alpha=0.2); ax.set_axisbelow(True)
    ax.legend(loc='upper left', bbox_to_anchor=(1.01, 1))
    fig.savefig(dest / 'all-runtime.png', dpi=180); fig.savefig(dest / 'all-runtime.svg'); plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4), layout='constrained')
    bars = ax.barh(y, [w['speedup'] for w in items], color='#228833')
    ax.bar_label(bars, fmt='%.2fx', padding=5)
    ax.set_xlim(0, max(w['speedup'] for w in items) * 1.2)
    ax.set_yticks(y, [w['title'] for w in items]); ax.invert_yaxis()
    ax.set_xlabel('Baseline median / final median')
    ax.set_title(f'Final speedup on the course VM ({repeat_label})')
    ax.grid(axis='x', alpha=0.2); ax.set_axisbelow(True)
    fig.savefig(dest / 'all-speedup.png', dpi=180); fig.savefig(dest / 'all-speedup.svg'); plt.close(fig)


def main():
    result = build_all(ROOT)  # Validate every batch before replacing any artifact.
    subprocess.run([sys.executable, str(ROOT / 'tools/summarize.py'), *LABELS], check=True)
    write_overview(result, ROOT / 'results')
    print(f"Validated {result['total_runs']} saved runs ({result['measured_runs']} measured, "
          f"{result['warmup_runs']} warmups); all five workloads summarized.")


if __name__ == '__main__':
    main()
