#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
[ "${1:-}" = --authorized ] || { echo 'Richiede autorizzazione esplicita dell’utente alla compilazione ISO.' >&2; exit 2; }
[ "$(id -u)" = 0 ] || { echo 'Eseguire come root.' >&2; exit 2; }
python3 scripts/prepare-winre.py --build-iso
lb config
lb build
