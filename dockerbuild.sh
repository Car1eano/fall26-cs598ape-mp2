#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
IMAGE=${1:-vim/598ape}

docker build -t "$IMAGE" -f "$SCRIPT_DIR/docker/Dockerfile" "$SCRIPT_DIR/docker"
