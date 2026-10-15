"""Reject damaged saved evidence before it can be used in overview plots."""
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'tools'))
spec = importlib.util.spec_from_file_location('all_summary', REPO / 'tools/summarize_all.py')
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


class ImageSummaryTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        for label in ['silk-baseline', 'silk-final-repeat', 'silk-checks', 'memory-silk-asan-repeat']:
            shutil.copytree(REPO / 'results' / label, self.root / 'results' / label,
                            ignore=shutil.ignore_patterns('source', '__pycache__', '*.svg', '*.py'))
        (self.root / 'benchmark').mkdir()
        shutil.copyfile(REPO / 'benchmark/silk-waves.png', self.root / 'benchmark/silk-waves.png')

    def evaluate(self):
        return tool.image_pair('silk', 'silk-final-repeat', 'silk-waves.png', self.root)

    def test_measured_statistics_exclude_warmup(self):
        baseline, final = self.evaluate()
        self.assertEqual(baseline['internal_seconds']['median'], 426.405388921)
        self.assertEqual(final['internal_seconds']['median'], 38.585800483)
        self.assertEqual(final['n'], 3)

    def test_changed_png_is_rejected(self):
        (self.root / 'results/silk-final-repeat/silk-wave-1.png').write_bytes(b'changed image')
        with self.assertRaisesRegex(ValueError, 'PNG hash mismatch'):
            self.evaluate()

    def test_changed_raw_formula_is_rejected(self):
        path = self.root / 'results/silk-final-repeat/silk-wave-1.rkt'
        path.write_text(path.read_text() + '\n; changed formula\n')
        with self.assertRaisesRegex(ValueError, 'raw output hash mismatch'):
            self.evaluate()

    def test_stale_statistics_are_rejected(self):
        path = self.root / 'results/silk-checks/checks.json'
        value = json.loads(path.read_text())
        value['stages']['silk-final-repeat']['median_seconds'] = 1.0
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, 'statistics differ'):
            self.evaluate()

    def test_diagnostic_errors_are_rejected(self):
        (self.root / 'results/memory-silk-asan-repeat/silk-wave.log').write_text('sanitizer error')
        with self.assertRaisesRegex(ValueError, 'diagnostic has errors'):
            self.evaluate()

    def test_failed_validation_preserves_existing_artifacts(self):
        path = self.root / 'results/all-summary.json'
        path.write_bytes(b'keep existing artifact')
        with patch.object(tool, 'build_all', side_effect=ValueError('invalid image evidence')), \
             patch.object(tool.subprocess, 'run') as command:
            with self.assertRaisesRegex(ValueError, 'invalid image evidence'):
                tool.main()
            command.assert_not_called()
        self.assertEqual(path.read_bytes(), b'keep existing artifact')


if __name__ == '__main__':
    unittest.main()
