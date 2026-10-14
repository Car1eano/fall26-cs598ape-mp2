#!/bin/sh
set -eu

IMAGE=${1:-vim/598ape}
docker run --rm -it --user "$(id -u):$(id -g)" \
    --security-opt seccomp=unconfined -v "$(pwd)":/host \
    --workdir /host "$IMAGE" /bin/bash
