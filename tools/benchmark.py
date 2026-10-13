#!/usr/bin/env python3
"""Build an isolated commit and preserve sequential benchmark observations."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
BASELINE = 'f19cc633664c9a333b208049770424d58d14909e'
FLAGS = '-std=c++17 -Wall -Wextra -I include -I.'


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--ref', default=BASELINE)
    p.add_argument('--label', required=True)
    p.add_argument('--flags', default=FLAGS)
    p.add_argument('--repeats', type=int, default=3)
    p.add_argument('--datasets', nargs='+', default=['diabetes', 'cancer', 'housing'])
    p.add_argument('--stack-candidate', action='store_true', help='Independent stack ablation on original source')
    a = p.parse_args()
    if a.repeats < 1 or not re.fullmatch(r'[A-Za-z0-9_-]+', a.label):
        p.error('Use positive repeats and a simple label')
    dest = ROOT / 'results' / a.label
    dest.mkdir(parents=True, exist_ok=False)
    source = dest / 'source'
    source.mkdir()
    archive = subprocess.check_output(['git', 'archive', a.ref], cwd=ROOT)
    run(['tar', '-x', '-C', str(source)], input=archive)
    if a.stack_candidate:
        path = source / 'src/reg_stack.h'
        text = path.read_text()
        start = text.index('    for (int i = MaxSize - 1;')
        end = text.index('\n  }', start)
        text = text[:start] + '    if (!full()) regs_[elements_++] = val;' + text[end:]
        start = text.index('    for (int i = 0; i < MaxSize; ++i) {', text.index('  DataT pop()'))
        end = text.index('\n  }', start)
        text = text[:start] + '    return empty() ? DataT(0) : regs_[--elements_];' + text[end:]
        path.write_text(text)
    sha = subprocess.check_output(['git', 'rev-parse', a.ref], cwd=ROOT, text=True).strip()
    metadata = {'commit': sha, 'flags': a.flags, 'stack_candidate': a.stack_candidate,
                'started_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                'command': ['./genetic_benchmark', '<dataset>'],
                'repeats': a.repeats, 'warmups': 1, 'datasets': a.datasets,
                'source_files': {str(f.relative_to(source)): hashlib.sha256(f.read_bytes()).hexdigest()
                                 for folder in ['src', 'include', 'benchmark']
                                 for f in (source / folder).iterdir() if f.is_file()}}
    (dest / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    with (dest / 'build.log').open('w') as log:
        run(['make', '-j2', 'CXXFLAGS=' + a.flags], cwd=source, stdout=log, stderr=subprocess.STDOUT)
    records = []
    # One process at a time: do not benchmark competing variants concurrently.
    for dataset in a.datasets:
        expected = None
        for i in range(a.repeats + 1):
            stem = f'{dataset}-' + ('warmup' if i == 0 else str(i))
            start = time.perf_counter()
            with (dest / (stem + '.rkt')).open('w') as out, (dest / (stem + '.stderr')).open('w') as err:
                proc = subprocess.run(['./genetic_benchmark', dataset], cwd=source, stdout=out, stderr=err)
            wall = time.perf_counter() - start
            text = (dest / (stem + '.rkt')).read_text()
            normalized = ''.join(line for line in text.splitlines(keepends=True) if not line.startswith(';;Time'))
            digest = hashlib.sha256(normalized.encode()).hexdigest()
            if expected is None:
                expected = digest
            timing = re.search(r';;Time\([^\n]+\) = ([0-9.]+) sec', text)
            record = {'dataset': dataset, 'run': i, 'warmup': i == 0, 'returncode': proc.returncode,
                      'wall_seconds': wall, 'internal_seconds': float(timing[1]) if timing else None,
                      'output_sha256': digest, 'matches_warmup': digest == expected,
                      'quality': [line for line in text.splitlines() if line.startswith(';;-')]}
            records.append(record)
            (dest / 'runs.json').write_text(json.dumps(records, indent=2) + '\n')
            print(a.label, dataset, i, f'wall={wall:.3f}', record['internal_seconds'], flush=True)
            if proc.returncode or not timing or digest != expected:
                raise RuntimeError('Failed run or nondeterministic output; inspect saved evidence')


if __name__ == '__main__':
    main()
