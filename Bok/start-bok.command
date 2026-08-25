#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
VAULT_DIR="${SCRIPT_DIR:h}"
export PYTHONPATH="$SCRIPT_DIR"
export PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/bok-pycache"
exec /usr/bin/python3 -m bok_core --vault "$VAULT_DIR" serve
