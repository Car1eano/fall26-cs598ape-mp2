#!/usr/bin/env python3
"""gprof fallback when perf is unavailable; never use these runs as timings."""
import argparse
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--source', required=True, type=Path)
    p.add_argument('--label', required=True)
    p.add_argument('--dataset', default='diabetes')
    p.add_argument('--optimization', default='-O0')
    a = p.parse_args()
    source = a.source.resolve()
    dest = ROOT / 'results' / a.label
    dest.mkdir(parents=True, exist_ok=False)
    binary = dest / 'profile-binary'
    cmd = ['g++', '-std=c++17', a.optimization, '-pg', '-g', '-Iinclude', '-I.',
           'benchmark/genetic_benchmark.cpp', *[str(f.relative_to(source)) for f in sorted((source / 'src').glob('*.cpp'))],
           '-o', str(binary)]
    (dest / 'command.txt').write_text(repr(cmd) + '\n')
    with (dest / 'build.log').open('w') as log:
        subprocess.run(cmd, cwd=source, stdout=log, stderr=subprocess.STDOUT, check=True)
    with (dest / 'output.rkt').open('w') as out, (dest / 'stderr.txt').open('w') as err:
        subprocess.run([str(binary), a.dataset], cwd=source, stdout=out, stderr=err, check=True)
    gmon = source / 'gmon.out'
    with (dest / 'gprof.txt').open('w') as report:
        subprocess.run(['gprof', str(binary), str(gmon)], stdout=report, check=True)
    gmon.rename(dest / 'gmon.out')
    print('Saved profile:', dest, flush=True)


if __name__ == '__main__':
    main()
