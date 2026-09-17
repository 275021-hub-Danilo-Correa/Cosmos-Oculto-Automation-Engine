#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
if [ -x .venv/bin/python ]; then
  exec .venv/bin/python iniciar.py "$@"
else
  exec python3 iniciar.py "$@"
fi
