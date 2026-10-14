#!/usr/bin/env python3
"""Build independent checks against an isolated benchmark source tree."""
import argparse
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--source', required=True, type=Path)
    p.add_argument('--label', required=True)
    p.add_argument('--optimization', default='-O2')
    p.add_argument('--sanitize', action='store_true')
    p.add_argument('--sorting', action='store_true')
    a = p.parse_args()
    source = a.source.resolve()
    dest = ROOT / 'results' / a.label
    dest.mkdir(parents=True, exist_ok=False)
    flags = ['-std=c++17', a.optimization, '-g', '-I' + str(source / 'include'), '-I' + str(source)]
    if a.sanitize:
        flags += ['-fsanitize=address,undefined', '-fno-omit-frame-pointer']
    env = os.environ.copy()
    if a.sanitize:
        env.update(ASAN_OPTIONS='detect_leaks=1:halt_on_error=1',
                   UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    records = []
    for name in ['stack', 'evaluation'] + (['sorting'] if a.sorting else []):
        binary = dest / (name + '-test')
        cmd = ['g++', *flags, str(ROOT / 'tests' / (name + '_test.cpp'))]
        if name != 'stack':
            cmd += [str(f) for f in sorted((source / 'src').glob('*.cpp'))]
        cmd += ['-o', str(binary)]
        with (dest / (name + '-build.log')).open('w') as log:
            subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, check=True)
        with (dest / (name + '-run.log')).open('w') as log:
            proc = subprocess.run([str(binary)], stdout=log, stderr=subprocess.STDOUT, env=env)
        records.append({'test': name, 'build_command': cmd, 'returncode': proc.returncode})
        (dest / 'checks.json').write_text(json.dumps(records, indent=2) + '\n')
        proc.check_returncode()
        print(name, 'passed', flush=True)
    (dest / 'flags.txt').write_text(repr(flags) + '\n')


if __name__ == '__main__':
    main()
