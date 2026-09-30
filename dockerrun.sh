#!/bin/sh
set -eu

IMAGE=${1:-vim/598ape}
docker run -it --security-opt seccomp=unconfined -v "$(pwd)":/host "$IMAGE" /bin/bash
