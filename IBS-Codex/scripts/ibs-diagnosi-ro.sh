#!/usr/bin/env bash
# Raccolta locale: nessuna scrittura sui dischi cliente, report nella Live.
set -u
umask 077
OUT="${1:-${HOME:-/tmp}/Desktop/IBS-Diagnosi-$(date +%Y%m%d-%H%M%S).txt}"
mkdir -p -- "$(dirname -- "$OUT")"
{ 
echo "IBS Diagnosi read-only — $(date -Is)"
echo "Host: $(hostname)"
echo "=== lsblk ==="
lsblk -e 7 -o NAME,PATH,MODEL,SIZE,TYPE,FSTYPE,RO,MOUNTPOINTS,TRAN 2>&1 || true
echo "=== mountpoint attivi (attenzione: RW preesistenti) ==="
findmnt -rn -o SOURCE,TARGET,FSTYPE,OPTIONS 2>&1 || true
echo "=== dischi & partizioni ==="
while IFS= read -r d; do
 echo "--- $d ---"
 if command -v sfdisk >/dev/null; then sfdisk --dump "$d" 2>&1 || true; fi
 if command -v smartctl >/dev/null; then smartctl -a "$d" 2>&1 || true; fi
done < <(lsblk -dn -e 7 -o PATH,TYPE | awk '$2=="disk"{print $1}')
echo "=== messaggi kernel STORAGE (estratto) ==="
dmesg 2>&1 | grep -Ei 'nvme|ata[0-9]|i/o error|blk_update|reset|medium error' | tail -150 || true
echo "Fine acquisizione. Nessuna riparazione eseguita."
} > "$OUT" 2>&1
printf 'Report salvato: %s\n' "$OUT"
