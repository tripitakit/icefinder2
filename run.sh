#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_BIN="$ROOT_DIR/.venv/bin"
PYTHON_BIN="$VENV_BIN/python"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Missing $PYTHON_BIN" >&2
  echo "Create the virtual environment first:" >&2
  echo "  python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt" >&2
  echo "or:" >&2
  echo "  uv venv .venv && uv pip install --python .venv/bin/python --prerelease=allow -r requirements.txt" >&2
  exit 1
fi

export PATH="$VENV_BIN:$PATH"
cd "$ROOT_DIR"

exec "$PYTHON_BIN" ICEfinder2.py "$@"
