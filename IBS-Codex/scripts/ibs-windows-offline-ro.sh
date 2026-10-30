#!/usr/bin/env bash
# Esame offline di Windows, SOLO se il volume e' gia' montato read-only.
# Non monta, non modifica, non esegue binari del cliente.
set -u
if [ "$#" -ne 1 ]; then echo "Uso: $0 /percorso/windows-montato-ro" >&2; exit 2; fi
ROOT="$(readlink -f -- "$1")"
if [ ! -d "$ROOT/Windows/System32" ]; then echo "Directory Windows non trovata" >&2; exit 2; fi
OPTIONS="$(findmnt -rn -T "$ROOT" -o OPTIONS 2>/dev/null || true)"
case ",$OPTIONS," in *,ro,*) ;; *) echo "RIFIUTATO: filesystem non montato in sola lettura" >&2; exit 3;; esac
umask 077
OUT="${HOME:-/tmp}/Desktop/IBS-Windows-Offline-$(date +%Y%m%d-%H%M%S).txt"
mkdir -p -- "$(dirname "$OUT")"
{
 echo "Diagnosi Windows offline read-only — $(date -Is)"
 echo "Percorso Windows omesso per minimizzazione dati cliente"
 echo "Opzioni mount: $OPTIONS"
 echo "=== file di sistema chiave (metadati, non contenuti personali) ==="
 for p in Windows/System32/config/SYSTEM Windows/System32/config/SOFTWARE Windows/System32/winload.efi Windows/System32/drivers; do
   if [ -e "$ROOT/$p" ]; then stat -c '%n | %s byte | %y | %F' "$ROOT/$p" | sed "s|$ROOT/||"; else echo "Assente: $p"; fi
 done
 echo "=== Log Windows presenti (metadata soltanto) ==="
 for p in Windows/Logs/CBS/CBS.log Windows/Logs/DISM/dism.log Windows/System32/winevt/Logs/System.evtx Windows/Minidump; do
  if [ -e "$ROOT/$p" ]; then stat -c '%n | %s byte | %y | %F' "$ROOT/$p" | sed "s|$ROOT/||"; else echo "Assente: $p"; fi
 done
 echo "=== possibili operazioni pendenti ==="
 for p in Windows/WinSxS/pending.xml Windows/System32/config/COMPONENTS; do
  [ ! -e "$ROOT/$p" ] || stat -c '%n | %s byte | %y' "$ROOT/$p" | sed "s|$ROOT/||"
 done
 echo "Nessun file cliente modificato; nessuna scansione antivirus eseguita."
} > "$OUT"
echo "Report: $OUT"
