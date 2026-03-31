#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_BIN="$ROOT_DIR/.venv/bin"
PYTHON_BIN="$VENV_BIN/python"
cd "$ROOT_DIR"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Missing $PYTHON_BIN" >&2
  echo "Create the virtual environment first with requirements.txt" >&2
  exit 1
fi

export PATH="$VENV_BIN:$PATH"

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  cat <<EOF
Usage: ./run-metagenome.sh [input_file] [extra ICEfinder args]

Runs ICEfinder with type 'Metagenome'.
EOF
  exit 0
fi

if [[ $# -eq 0 || "${1:-}" == -* ]]; then
  echo "Missing input file." >&2
  echo "Usage: ./run-metagenome.sh [input_file] [extra ICEfinder args]" >&2
  exit 1
fi

INPUT_FILE="$1"
shift

if [[ ! -f "$INPUT_FILE" ]]; then
  echo "Input file not found: $INPUT_FILE" >&2
  exit 1
fi

echo "Running metagenome input '$INPUT_FILE' with Kraken2; this can take a long time depending on the configured DB size." >&2
exec "$PYTHON_BIN" ICEfinder2.py -i "$INPUT_FILE" -t Metagenome "$@"
