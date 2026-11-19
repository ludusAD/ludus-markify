#!/usr/bin/env bash
# Build the frontend into the Python package, then build the wheel + sdist.
set -e
cd "$(dirname "$0")/.."
(cd frontend && npm ci && npm run build -- --outDir ../ludus_markify/static --emptyOutDir)
if [ "$1" = "--wheel" ]; then
  python3 -m pip install --quiet build   # run inside a venv
  rm -rf dist
  python3 -m build
fi
