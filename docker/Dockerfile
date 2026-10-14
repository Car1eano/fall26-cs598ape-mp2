FROM ubuntu:24.04

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        binutils g++ gdb git make python3 python3-venv tar valgrind \
        linux-tools-common linux-tools-generic racket fonts-dejavu-core \
        libglib2.0-0t64 libcairo2 libpango-1.0-0 libpangocairo-1.0-0 \
        libjpeg-turbo8 libpng16-16t64 \
    && rm -rf /var/lib/apt/lists/*

COPY tools/plot-requirements.txt /tmp/plot-requirements.txt

RUN python3 -m venv /opt/mp2-venv \
    && /opt/mp2-venv/bin/pip install --no-cache-dir -r /tmp/plot-requirements.txt \
    && rm /tmp/plot-requirements.txt

ENV PATH="/opt/mp2-venv/bin:${PATH}"
ENV MPLCONFIGDIR=/tmp/mp2-matplotlib

# Check headless Racket and Python PNG rendering during the build.
RUN racket -e '(require racket/draw) (unless (send (make-bitmap 2 2) save-file "/tmp/racket-smoke.png" (quote png)) (error "PNG rendering failed"))' \
    && test -s /tmp/racket-smoke.png \
    && rm /tmp/racket-smoke.png \
    && python3 -c 'import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt; plt.plot([0, 1], [0, 1]); plt.savefig("/tmp/python-smoke.png")' \
    && test -s /tmp/python-smoke.png \
    && rm /tmp/python-smoke.png \
    && rm -rf /tmp/mp2-matplotlib

# Use the installed perf binary rather than the host-kernel lookup wrapper.
RUN for perf_binary in /usr/lib/linux-tools/*/perf; do \
        if [ -x "$perf_binary" ]; then \
            ln -s "$perf_binary" /usr/local/bin/perf; break; \
        fi; \
    done \
    && perf --version

WORKDIR /host
