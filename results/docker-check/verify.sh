#!/bin/bash
set -euo pipefail

mkdir /tmp/mp2-check-source
cp /host/Makefile /tmp/mp2-check-source/
cp -r /host/src /host/include /host/benchmark /host/tools /host/tests /tmp/mp2-check-source/
cd /tmp/mp2-check-source

{
    cat /etc/os-release
    id
    g++ --version
    make --version
    git --version
    python3 --version
    racket --version
    valgrind --version
    gprof --version
    gdb --version
    perf --version
    python3 -c 'import matplotlib, numpy; print("matplotlib", matplotlib.__version__); print("numpy", numpy.__version__)'
} > /checks/environment.log 2>&1

make -j2 > /checks/compile.log 2>&1
./genetic_benchmark diabetes > /checks/diabetes.rkt 2> /checks/diabetes.stderr
racket /checks/diabetes.rkt > /checks/racket-module.stdout 2> /checks/racket-module.stderr

python3 -m unittest discover -s tests -p benchmark_tools_test.py -v \
    > /checks/python-tests.log 2>&1
python3 tools/check.py --source . --label docker-unit-check --sanitize --sorting --mutations --distributions \
    > /checks/cpp-tests.log 2>&1
cp results/docker-unit-check/checks.json /checks/unit-checks.json
cp results/docker-unit-check/flags.txt /checks/unit-flags.txt
cp results/docker-unit-check/*.log /checks/

valgrind --leak-check=full --show-leak-kinds=all \
    --errors-for-leak-kinds=definite,indirect --error-exitcode=99 \
    ./genetic_benchmark diabetes > /checks/valgrind-diabetes.rkt 2> /checks/valgrind-diabetes.log

cat > /tmp/gprof-smoke.cpp <<'CPP'
int square(int x) { return x * x; }
int main() {
    volatile int result = 0;
    for (int i = 0; i < 1000000; ++i) result = square(i % 100);
    return result < 0;
}
CPP
g++ -std=c++17 -O0 -g -pg /tmp/gprof-smoke.cpp -o /tmp/gprof-smoke
(cd /tmp && ./gprof-smoke)
gprof /tmp/gprof-smoke /tmp/gmon.out > /checks/gprof-smoke.txt

set +e
perf stat -e task-clock true > /checks/perf.stdout 2> /checks/perf.stderr
perf_status=$?
set -e
printf '%s\n' "$perf_status" > /checks/perf-exit-code.txt
if [ "$perf_status" -ne 0 ] && ! grep -qiE 'permission|access.*limited' /checks/perf.stderr; then
    cat /checks/perf.stderr
    exit "$perf_status"
fi

python3 - <<'PY'
import importlib.util
from pathlib import Path
spec = importlib.util.spec_from_file_location('summary_tool', Path('tools/summarize.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
summary, _ = module.build_summary(['baseline', 'o2', 'stack', 'o2-stack', 'sorted', 'hoist-fixed', 'final'], Path('/host/results'))
assert len(summary) == 21
Path('/checks/saved-records-validation.txt').write_text('All seven stages validated in the container; charts were not regenerated.\n')
PY

printf 'Docker checks passed.\n'
