#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
SHELLCHECK=${SHELLCHECK:-shellcheck}
if command -v "$SHELLCHECK" >/dev/null; then
    # Unchanged TeamViewer and ISO-list scripts have pre-existing unused-variable warnings.
    mapfile -d '' SCRIPTS < <(python3 - <<'PY'
from pathlib import Path
import sys
for p in Path('config').rglob('*'):
    if p.is_file() and (p.read_bytes().startswith(b'#!/bin/bash') or p.suffix == '.sh'):
        if p.name not in {'ibs-teamviewer-auto', 'ibs-iso-list'}:
            sys.stdout.buffer.write(str(p).encode() + b'\0')
PY
)
    "$SHELLCHECK" -x -S warning "${SCRIPTS[@]}" tests/check.sh
else
    echo 'ShellCheck opzionale non disponibile; sintassi e test Python completati.' >&2
fi
