#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
[ "${1:-}" = --authorized ] || { echo 'Richiede autorizzazione esplicita dell’utente alla compilazione ISO.' >&2; exit 2; }
[ "$(id -u)" = 0 ] || { echo 'Eseguire come root.' >&2; exit 2; }
test -f config/includes.chroot/opt/ibs/codex/codex || {
    echo 'Preparare prima Codex verificato nella copia nuova: python3 scripts/prepare-codex.py' >&2
    exit 2
}
package=config/includes.chroot/tmp/teamviewer-host.deb
if [ ! -f "$package" ]; then
    [ -f .build/teamviewer-host.deb ] || { echo 'Manca il pacchetto TeamViewer Host 15.82.6 verificato in .build/teamviewer-host.deb' >&2; exit 2; }
    install -D -m 0644 .build/teamviewer-host.deb "$package"
fi
python3 scripts/prepare-winre.py --build-iso
lb config
lb build
