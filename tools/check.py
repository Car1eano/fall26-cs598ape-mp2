#!/usr/bin/env python3
"""Build independent checks against an isolated benchmark source tree."""
import argparse
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--source', required=True, type=Path)
    p.add_argument('--label', required=True)
    p.add_argument('--optimization', default='-O2')
    p.add_argument('--sanitize', action='store_true')
    a = p.parse_args()
    source = a.source.resolve()
    dest = ROOT / 'results' / a.label
    dest.mkdir(parents=True, exist_ok=False)
    flags = ['-std=c++17', a.optimization, '-g', '-I' + str(source / 'include'), '-I' + str(source)]
    if a.sanitize:
        flags += ['-fsanitize=address,undefined', '-fno-omit-frame-pointer']
    for name in ['stack', 'evaluation']:
        binary = dest / (name + '-test')
        cmd = ['g++', *flags, str(ROOT / 'tests' / (name + '_test.cpp'))]
        if name == 'evaluation':
            cmd += [str(f) for f in sorted((source / 'src').glob('*.cpp'))]
        cmd += ['-o', str(binary)]
        with (dest / (name + '-build.log')).open('w') as log:
            subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, check=True)
        with (dest / (name + '-run.log')).open('w') as log:
            subprocess.run([str(binary)], stdout=log, stderr=subprocess.STDOUT, check=True)
        print(name, 'passed', flush=True)
    (dest / 'flags.txt').write_text(repr(flags) + '\n')


if __name__ == '__main__':
    main()
