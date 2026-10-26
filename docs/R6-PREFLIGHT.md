# R6 — prerequisiti del futuro collaudo WinRE

Verifica del 26 ottobre 2026 nel solo progetto `/opt/ibs-recoverywin-1.0`.
Branch iniziale `ibs-recoverywin-1.0`, checkout pulita. R5 non ripetuta.
Nessuna VM avviata, nessuna ISO compilata, nessun disco fisico modificato.

## Disponibilità osservata

- `/usr/bin/qemu-system-x86_64` e `/usr/bin/qemu-img`: 10.0.13,
  Debian `1:10.0.13+ds-0+deb13u1`. Solo interrogazione delle versioni.
- `/dev/kvm` assente: accelerazione KVM non disponibile in questo ambiente.
  Futuro uso TCG da concordare esplicitamente, incluso limite temporale.
- `df -h`: filesystem da 94 GiB, 44 GiB usati, circa 46 GiB disponibili,
  49% occupato, sia per progetto sia per `/opt/ibs-recoverywin-test`.
  Dato istantaneo, non prenotazione di spazio.
- Pacchetto host `ovmf`: `2025.02-8+deb13u1`. File regolari
  `/usr/share/OVMF/OVMF_CODE_4M.fd` (3653632 byte) e
  `/usr/share/OVMF/OVMF_VARS_4M.fd` (540672 byte), entrambi con firma `_FVH`
  all'offset 40; coppia standard 4M coerente del pacchetto x86_64.
  SHA-256 CODE: `624e06de18b4fa535e90db7160d00d3d07d206422b89999bf1e27d920264e4e0`.
  SHA-256 VARS: `5d2ac383371b408398accee7ec27c8c09ea5b74a0de0ceea6513388b15be5d1e`.
  Non copiata né usata per avviare VM. Nessuna coppia reale individuata nel
  progetto o nella directory test dalla ricerca fino a profondità 3;
  due vecchie directory fixture non leggibili. R5 richiede firmware reali
  nel progetto: questo prerequisito resta da soddisfare prima del boot.
- Ricerca ricorsiva di file `*.iso` esclusivamente nel progetto e in
  `/opt/ibs-recoverywin-test`: trovate solo ISO IBS R2/R3 e copie di build,
  comprese `live-image-amd64.hybrid.iso` e le immagini TEST datate 25 ottobre.
  Nessuna candidata WinRE identificata. La ricerca non è esaustiva nelle
  directory chroot/cache e fixture con permesso negato. Nessuna ISO aperta
  o selezionata in sostituzione; nessuna ricerca su NAS, USB o device.

## Preflight ripetibile, senza boot

`scripts/preflight-r6-winre.py` richiede tutti i percorsi assoluti espliciti:

```text
python3 scripts/preflight-r6-winre.py --iso /percorso/WinRE.iso \
  --iso-sha256 HASH_ATTESO --code /percorso/OVMF_CODE_4M.fd \
  --vars /percorso/OVMF_VARS_4M.fd --base /percorso/base.qcow2 \
  --overlay /percorso/overlay.qcow2
```

I segnaposto non sono un comando di lancio. ISO, provenienza e hash atteso
vanno ancora indicati e autorizzati dall'utente. Lo script non li sceglie.
Controlla file regolari, componenti senza symlink, ruoli senza hardlink,
filesystem locali consentiti, mount USB/rimovibili rilevabili e rifiuta
filesystem di rete/sconosciuti, `/dev`, `/proc`, `/sys`, `/mnt`, `/media`,
`/run/media`, percorsi relativi e `..`. Rifiuta anche device composti con
slaves, per i quali la provenienza non sarebbe verificabile direttamente.
Controlla hash ISO e descrittore ISO9660, dimensioni coppia firmware 2M/4M
con firma FV, header QCOW2, assenza di cifratura/feature incompatibili,
base senza backing e overlay con unico riferimento assoluto alla base
esplicita. Prima di interrogare qemu-img rifiuta riferimenti inattesi.
`qemu-img check` senza riparazione e `info` usano backend JSON espliciti
con backing nullo: non seguono catene arbitrarie. Controlla integrità e
uguaglianza delle dimensioni virtuali. Nessun comando create/resize/repair
nello script preflight; nessuna esecuzione di qemu-system.

Limiti: controlli strutturali e hash non attestano contenuto WinRE,
avviabilità, architettura o autenticità dei firmware; firme e dimensioni
non sostituiscono provenienza verificata. Il mount namespace deve essere
attendibile: overlay/bind possono nascondere la provenienza sottostante.
Non è una protezione contro sostituzioni concorrenti dei file: eseguire
su directory private, senza altri scrittori, e rivalidare al futuro lancio.
Il risultato riporta spazio libero, senza garantire capienza del futuro
carico. Nessun preflight completo reale è stato eseguito: manca la ISO.

## Prove eseguite

`python3 scripts/test-r6-preflight.py`: 12 test offline passati, con file
sintetici e QCOW2 fittizie in directory temporanee nel progetto, rimosse
alla fine. Non richiedono privilegi. qemu-img crea solo le fixture dei test.
Coprono percorso valido e hash invariati dopo il controllo, percorsi
vietati/mancanti/relativi, directory, FIFO, symlink, mount NFS/USB simulati,
hash e struttura ISO errati, firmware errato, backing inatteso respinto
prima di qemu-img, header corrotto, dimensioni discordanti, hardlink e
uscita CLI nonzero. Il successo su firmware e ISO sintetici è soltanto
una prova del validatore, non prova di boot.

Compilazione sintattica Python e `git diff --check` completati senza errori.
Nessuna lunga procedura R2–R5 ripetuta; timer, runner, servizi,
TeamViewer/SSH, credenziali, pacchetti e rete non modificati.

## Piano successivo, subordinato ad autorizzazione

Applicare R5: sessione privata sotto `.build`, utente non root, hash e
provenienza approvati, CODE/ISO/base in sola lettura e copia VARS privata.
Creare soltanto dopo autorizzazione una base vuota e un overlay QCOW2,
collegando esclusivamente l'overlay come unico disco guest. Rivalidare
input e catena. Preparare e revisionare argv q35/OVMF, acceleratore
esplicito, `-no-user-config -nodefaults`, CD-ROM RO, rete `-nic none`,
nessun passthrough USB/PCI o condivisione. QMP Unix privato e avvio `-S`,
verifica backend prima di `cont`, timeout totale 10 minuti e cleanup
con reap garantito secondo R5. Annotare separatamente boot OVMF e WinRE,
poi verificare hash protetti e integrità overlay dopo arresto.

Stop attuale: nessun boot WinRE/Windows autorizzato o dichiarato; nessuna
base o overlay di collaudo reale creata da R6, solo fixture temporanee.
