import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('summary_tool', Path(__file__).resolve().parents[1] / 'tools/summarize.py')
summary_tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(summary_tool)


class BenchmarkToolsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.results = self.root / 'results'
        self.results.mkdir()
        self.write_batch('baseline', [1.0, 3.0, 2.0])
        self.write_batch('candidate', [0.5, 1.5, 1.0])

    def write_batch(self, label, times, expression='1'):
        directory = self.results / label
        directory.mkdir(exist_ok=True)
        metadata = {'repeats': 3, 'warmups': 1, 'datasets': summary_tool.DATASETS,
                    'flags': '-std=c++17 -O2',
                    'source_files': {'benchmark/' + d + '.csv': 'data-' + d for d in summary_tool.DATASETS}}
        (directory / 'metadata.json').write_text(json.dumps(metadata))
        records = []
        for dataset in summary_tool.DATASETS:
            quality = [';;- Length: 1 nodes', ';;- Depth: 0', ';;- Raw fitness: 1', ';;- Test MSE: 1'] * 2
            body = '#lang racket\n' + '\n'.join(quality) + '\n(define prediction ' + expression + ')\n'
            digest = hashlib.sha256(body.encode()).hexdigest()
            for i, seconds in enumerate([100.0, *times]):
                stem = dataset + '-' + ('warmup' if i == 0 else str(i))
                (directory / (stem + '.rkt')).write_text(body + f';;Time(Test) = {seconds:.9f} sec\n')
                (directory / (stem + '.stderr')).write_text('')
                records.append({'dataset': dataset, 'run': i, 'warmup': i == 0, 'returncode': 0,
                                'internal_seconds': seconds, 'wall_seconds': seconds + 0.2,
                                'output_sha256': digest, 'quality': quality, 'matches_warmup': True})
        (directory / 'runs.json').write_text(json.dumps(records))

    def edit_json(self, filename, edit):
        path = self.results / 'candidate' / filename
        value = json.loads(path.read_text())
        edit(value)
        path.write_text(json.dumps(value))

    def evaluate(self):
        return summary_tool.build_summary(['baseline', 'candidate'], self.results)[0]

    def test_warmup_excluded_and_statistics(self):
        rows = self.evaluate()
        self.assertEqual(rows[0]['internal_seconds'], {'median': 2.0, 'mean': 2.0, 'min': 1.0,
                                                      'max': 3.0, 'sample_stdev': 1.0})
        self.assertEqual(rows[3]['speedup'], 2.0)
        self.assertEqual(rows[0]['n'], 3)

    def test_raw_output_is_rechecked(self):
        path = self.results / 'candidate' / 'diabetes-1.rkt'
        path.write_text(path.read_text().replace('prediction 1', 'prediction 2'))
        with self.assertRaisesRegex(ValueError, 'raw output hash mismatch'):
            self.evaluate()

    def test_different_formulas_rejected(self):
        self.write_batch('candidate', [0.5, 1.5, 1.0], expression='2')
        with self.assertRaisesRegex(ValueError, 'output differs from baseline'):
            self.evaluate()

    def test_dataset_mismatch_rejected(self):
        self.edit_json('metadata.json', lambda m: m['source_files'].update({'benchmark/diabetes.csv': 'different'}))
        with self.assertRaisesRegex(ValueError, 'dataset hash differs'):
            self.evaluate()

    def test_missing_run_rejected(self):
        self.edit_json('runs.json', lambda rows: rows.pop())
        with self.assertRaisesRegex(ValueError, 'incomplete or extra'):
            self.evaluate()

    def test_duplicate_run_rejected(self):
        self.edit_json('runs.json', lambda rows: rows[2].update(run=1))
        with self.assertRaisesRegex(ValueError, 'missing or duplicate'):
            self.evaluate()

    def test_failed_run_rejected(self):
        self.edit_json('runs.json', lambda rows: rows[1].update(returncode=1))
        with self.assertRaisesRegex(ValueError, 'failed run'):
            self.evaluate()

    def test_nonfinite_wall_time_rejected(self):
        self.edit_json('runs.json', lambda rows: rows[1].update(wall_seconds=float('nan')))
        with self.assertRaisesRegex(ValueError, 'invalid wall_seconds'):
            self.evaluate()

    def test_instrumented_timings_rejected(self):
        self.edit_json('metadata.json', lambda m: m.update(flags='-O2 -pg'))
        with self.assertRaisesRegex(ValueError, 'instrumented runs'):
            self.evaluate()

    def test_recorded_time_checked_against_stdout(self):
        self.edit_json('runs.json', lambda rows: rows[1].update(internal_seconds=0.4))
        with self.assertRaisesRegex(ValueError, 'raw timing mismatch'):
            self.evaluate()

    def test_invalid_batch_does_not_overwrite_artifacts(self):
        self.write_batch('candidate', [0.5, 1.5, 1.0], expression='2')
        for name in ['summary.json', 'summary.md', 'runtime.png', 'speedup.png']:
            (self.results / name).write_bytes(b'keep existing artifact')
        with patch.object(summary_tool, 'ROOT', self.root), patch.object(sys, 'argv', ['summarize.py', 'baseline', 'candidate']):
            with self.assertRaises(ValueError):
                summary_tool.main()
        for name in ['summary.json', 'summary.md', 'runtime.png', 'speedup.png']:
            self.assertEqual((self.results / name).read_bytes(), b'keep existing artifact')


if __name__ == '__main__':
    unittest.main()
