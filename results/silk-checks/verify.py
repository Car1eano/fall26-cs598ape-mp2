"""Validate saved Silk waves runs and render their exported formulas on the VM."""
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import time

import matplotlib.image as mpimg
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DEST = Path(__file__).resolve().parent


def digest(data):
    return hashlib.sha256(data).hexdigest()


def normalized(path):
    return ''.join(line for line in path.read_text().splitlines(keepends=True)
                   if not line.startswith(';;Time')).encode()


def main():
    original = mpimg.imread(ROOT / 'benchmark/silk-waves.png')[..., :3]
    assert original.shape == (256, 256, 3)
    stages = {}
    reference = None
    reference_pixels = None
    for label in ['silk-baseline', 'silk-final-repeat']:
        folder = ROOT / 'results' / label
        metadata = json.loads((folder / 'metadata.json').read_text())
        runs = json.loads((folder / 'runs.json').read_text())
        assert metadata['datasets'] == ['silk-wave']
        assert metadata['repeats'] == 3 and metadata['warmups'] == 1
        assert [r['run'] for r in runs] == [0, 1, 2, 3]
        assert all(r['returncode'] == 0 and r['matches_warmup'] for r in runs)
        assert metadata['source_files']['benchmark/silk-waves.png'] == digest(
            (ROOT / 'benchmark/silk-waves.png').read_bytes())
        if label == 'silk-baseline':
            assert metadata['commit'] == 'f19cc633664c9a333b208049770424d58d14909e'
            assert metadata['flags'] == '-std=c++17 -Wall -Wextra -I include -I.'
        else:
            assert metadata['commit'] == '51324285ab91bd7b27998be74809728a1ce7c23e'
            assert metadata['flags'] == '-std=c++17 -O2 -Wall -Wextra -I include -I.'
        assert not metadata['stack_candidate']
        rendered = []
        for r in runs:
            stem = 'silk-wave-' + ('warmup' if r['warmup'] else str(r['run']))
            formula = folder / (stem + '.rkt')
            output = normalized(formula)
            assert digest(output) == r['output_sha256']
            assert (folder / (stem + '.stderr')).read_bytes() == b''
            assert r['wall_seconds'] >= r['internal_seconds'] > 0
            if reference is None:
                reference = output
            assert output == reference, f'Formula or quality changed: {label}/{stem}'
            png = folder / (stem + '.png')
            started = time.perf_counter()
            with (folder / (stem + '-render.stdout')).open('w') as out, \
                 (folder / (stem + '-render.stderr')).open('w') as err:
                subprocess.run(['racket', str(formula), str(png)],
                               stdout=out, stderr=err, check=True)
            render_seconds = time.perf_counter() - started
            assert (folder / (stem + '-render.stderr')).read_bytes() == b''
            pixels = mpimg.imread(png)[..., :3]
            assert pixels.shape == original.shape and np.isfinite(pixels).all()
            if reference_pixels is None:
                reference_pixels = pixels
            assert np.array_equal(pixels, reference_pixels), f'PNG pixels changed: {label}/{stem}'
            rendered.append({'run': r['run'], 'png_sha256': digest(png.read_bytes()),
                             'pixel_bytes_sha256': digest(pixels.tobytes()),
                             'render_wall_seconds': render_seconds,
                             'display_rgb_mse': float(np.mean((pixels.astype(np.float64) - original) ** 2))})
        measured = [r['internal_seconds'] for r in runs if not r['warmup']]
        stages[label] = {'metadata': metadata, 'seconds': measured,
                         'median_seconds': statistics.median(measured),
                         'min_seconds': min(measured), 'max_seconds': max(measured),
                         'mean_seconds': statistics.mean(measured),
                         'sample_stddev_seconds': statistics.stdev(measured),
                         'quality_lines': [line for line in reference.decode().splitlines()
                                           if 'MSE' in line and line.startswith(';;')],
                         'rendered': rendered}
    diagnostic = ROOT / 'results/memory-silk-asan-repeat'
    assert json.loads((diagnostic / 'checks.json').read_text()) == [
        {'dataset': 'silk-wave', 'command': ['./genetic_benchmark', 'silk-wave'], 'returncode': 0}]
    assert (diagnostic / 'silk-wave.log').read_bytes() == b''
    assert normalized(diagnostic / 'silk-wave.rkt') == reference
    fig, axes = plt.subplots(1, 3, figsize=(9, 3), constrained_layout=True)
    panel_pixels = [original,
                    mpimg.imread(ROOT / 'results/silk-baseline/silk-wave-1.png')[..., :3],
                    mpimg.imread(ROOT / 'results/silk-final-repeat/silk-wave-1.png')[..., :3]]
    for ax, pixels, title in zip(axes, panel_pixels,
                                 ['Original input', 'Baseline reconstruction', 'Optimized reconstruction']):
        ax.imshow(pixels)
        ax.set_title(title, fontsize=11)
        ax.axis('off')
    fig.savefig(DEST / 'comparison.png', dpi=180)
    fig.savefig(DEST / 'comparison.svg')
    plt.close(fig)
    speedup = stages['silk-baseline']['median_seconds'] / stages['silk-final-repeat']['median_seconds']
    result = {'complete': True, 'stages': stages, 'speedup': speedup,
              'formula_and_quality_identical': True, 'rendered_pixels_identical': True,
              'full_workload_asan_ubsan_passed': True,
              'diagnostic_results': 'results/memory-silk-asan-repeat',
              'failed_restricted_environment_attempt': 'results/memory-silk-asan',
              'racket_version': subprocess.check_output(['racket', '--version'], text=True).strip(),
              'render_times_in_search_statistics': False,
              'note': 'Display RGB MSE uses all rounded/clamped PNG pixels; exported test MSE uses the held-out float predictions.'}
    (DEST / 'checks.json').write_text(json.dumps(result, indent=2) + '\n')
    rows = ['| Version | Median seconds | Min–max seconds | Sample stddev |',
            '|---|---:|---:|---:|']
    for label, stage in stages.items():
        rows.append(f"| {label} | {stage['median_seconds']:.3f} | {stage['min_seconds']:.3f}–{stage['max_seconds']:.3f} | {stage['sample_stddev_seconds']:.3f} |")
    (DEST / 'summary.md').write_text('# Silk waves verification\n\n' + '\n'.join(rows) +
        f'\n\nMedian speedup: {speedup:.2f}x. One warmup and three measured runs per version.\n'
        'Formulas, reported MSE and reconstructed pixels match. Full-workload ASan/UBSan passed.\n'
        'Racket render times are recorded separately and excluded from search timings.\n')
    print(f'Silk waves checks passed; median speedup {speedup:.2f}x', flush=True)


if __name__ == '__main__':
    main()
