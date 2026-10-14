#!/usr/bin/env python3
"""Run full-workload memory diagnostics, separate from performance runs."""
import argparse
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--ref', required=True)
    p.add_argument('--label', required=True)
    p.add_argument('--mode', choices=['valgrind', 'sanitize'], required=True)
    p.add_argument('--datasets', nargs='+', default=['diabetes'])
    a = p.parse_args()
    dest = ROOT / 'results' / a.label
    dest.mkdir(parents=True, exist_ok=False)
    source = dest / 'source'
    source.mkdir()
    archive = subprocess.check_output(['git', 'archive', a.ref], cwd=ROOT)
    subprocess.run(['tar', '-x', '-C', str(source)], input=archive, check=True)
    flags = '-std=c++17 -O2 -g -Wall -Wextra -I include -I.'
    if a.mode == 'sanitize':
        flags += ' -fsanitize=address,undefined -fno-omit-frame-pointer'
    env = os.environ.copy()
    diagnostic_env = {}
    if a.mode == 'sanitize':
        diagnostic_env = {'ASAN_OPTIONS': 'detect_leaks=1:halt_on_error=1',
                          'UBSAN_OPTIONS': 'halt_on_error=1:print_stacktrace=1'}
        env.update(diagnostic_env)
    sha = subprocess.check_output(['git', 'rev-parse', a.ref], cwd=ROOT, text=True).strip()
    (dest / 'metadata.json').write_text(json.dumps({'commit': sha, 'mode': a.mode, 'flags': flags,
                                                  'datasets': a.datasets,
                                                  'environment': diagnostic_env}, indent=2) + '\n')
    with (dest / 'build.log').open('w') as log:
        subprocess.run(['make', '-j2', 'CXXFLAGS=' + flags], cwd=source, stdout=log, stderr=subprocess.STDOUT, check=True)
    records = []
    for dataset in a.datasets:
        cmd = ['./genetic_benchmark', dataset]
        if a.mode == 'valgrind':
            cmd = ['valgrind', '--leak-check=full', '--show-leak-kinds=all',
                   '--errors-for-leak-kinds=definite,indirect', '--error-exitcode=99', *cmd]
        with (dest / (dataset + '.rkt')).open('w') as out, (dest / (dataset + '.log')).open('w') as err:
            proc = subprocess.run(cmd, cwd=source, stdout=out, stderr=err, env=env)
        records.append({'dataset': dataset, 'command': cmd, 'returncode': proc.returncode})
        (dest / 'checks.json').write_text(json.dumps(records, indent=2) + '\n')
        print(a.mode, dataset, 'returncode', proc.returncode, flush=True)
    if any(r['returncode'] for r in records):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
