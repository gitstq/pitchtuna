#!/usr/bin/env bash
# PitchTuna launcher for macOS (double-clickable .command).
# Runs directly from the source tree (no install required), only needs numpy.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
cd "$DIR"

PYTHON="${PYTHON:-python3}"
if ! "$PYTHON" -c "import numpy" >/dev/null 2>&1; then
  echo "[pitchtuna] numpy not found; installing runtime dependency ..."
  "$PYTHON" -m pip install -r requirements.txt
fi

exec "$PYTHON" -m pitchtuna "$@"
