#!/usr/bin/env bash
set -euo pipefail

MODE="${DOG_NUITKA_MODE:-standalone}"
OUT_DIR="${DOG_BINARY_OUT_DIR:-dist-bin}"
NAME="${DOG_BINARY_NAME:-dog}"

case "$MODE" in
  standalone | onefile) ;;
  *)
    echo "DOG_NUITKA_MODE must be 'standalone' or 'onefile'" >&2
    exit 2
    ;;
esac

uv run python -m nuitka \
  --mode="$MODE" \
  --assume-yes-for-downloads \
  --remove-output \
  --output-dir="$OUT_DIR" \
  --output-filename="$NAME" \
  --include-package=dog_cli \
  --include-package=dog_core \
  --include-package=marko.ext \
  --python-flag=-m \
  --main=src/dog_cli
