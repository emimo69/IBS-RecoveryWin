# R7 — tentativo OVMF fermato dall'ambiente

26 ottobre 2026, progetto `/opt/ibs-recoverywin-1.0`, utente UID 1000.
Branch `ibs-recoverywin-1.0`, checkout iniziale pulita, HEAD `b331ed1`.
**Boot firmware OVMF non verificato.** Un solo tentativo runtime; nessun
successo WinRE o Windows dichiarato.

## Configurazione e comando

Eseguito `python3 scripts/test-r7-ovmf-boot.py` dalla radice del progetto.
QEMU: `QEMU emulator version 10.0.13 (Debian 1:10.0.13+ds-0+deb13u1)`.
Script senza input media: rifiuta argomenti, root e directory di lavoro
diversa dal progetto. Valida file firmware regolari, dimensioni, firma FV
e assenza di symlink. Directory privata creata con tempfile, modalità 0700.

Scelta consentita da R7: solo firmware, senza creare base/overlay QCOW2.
Dischi guest previsti: zero. Nessuna base da confrontare dopo il test.
Modello q35, TCG, RAM 256 MiB, VGA emulata con display disabilitato,
`-no-user-config -nodefaults -nic none -monitor none -S`.
CODE pflash raw readonly; solo copia privata VARS pflash raw scrivibile.
Nessuna ISO, passthrough, condivisione o backend `/dev`.
QMP Unix privato, seriale e stderr locali, nessun listener TCP/VNC.
L'argv completo è conservato nel risultato locale.

Il supervisore prevede watchdog totale 120 secondi (inferiore ai 10 minuti
autorizzati), connessione QMP entro 15 secondi, verifica query-status e
query-block prima di cont, controllo PCI, osservazione per 45 secondi,
query-status e screendump. Cleanup con wait, SIGTERM, SIGKILL e reap.
Queste fasi successive alla connessione non sono state raggiunte.

## Risultato effettivo e diagnosi

Artefatti conservati esclusivamente in `.build/r7-_d25mj95/`:
`result.json`, `qemu.log`, `VARS.fd`. Directory ignorata da Git.

QEMU ha riportato:

```text
Failed to bind socket to /opt/ibs-recoverywin-1.0/.build/r7-_d25mj95/qmp.sock: Operation not permitted
```

Anche il client socket ha ricevuto `PermissionError(1, 'Operation not permitted')`.
L'ambiente impedisce il canale QMP Unix richiesto. Nessuna escalation,
modifica sandbox o secondo tentativo. Durata misurata lancio/cleanup:
0,032 secondi. Processo PID 5 terminato con codice 1 e raccolto con wait;
nessun processo della prova lasciato in background.

Nessuna risposta query-status/query-block ottenuta, nessun cont inviato,
nessuna schermata o output UEFI osservato. Backend e assenza rete descritti
sopra sono quelli richiesti dall'argv, **non verificati via QMP**.

## Integrità e limiti

Percorsi originali invariati prima/dopo, SHA-256 uguali:

| File host | Byte | SHA-256 prima e dopo |
| --- | ---: | --- |
| `/usr/share/OVMF/OVMF_CODE_4M.fd` | 3653632 | `624e06de18b4fa535e90db7160d00d3d07d206422b89999bf1e27d920264e4e0` |
| `/usr/share/OVMF/OVMF_VARS_4M.fd` | 540672 | `5d2ac383371b408398accee7ec27c8c09ea5b74a0de0ceea6513388b15be5d1e` |

Non provati WinRE, TeamViewer, boot Windows o dischi fisici. Nessuna ISO
compilata, nessun pacchetto installato. R3, runner/timer, rete, SSH,
credenziali e codice di prodotto non modificati. Per osservare il boot
occorre un ambiente che consenta il socket privato richiesto: questo
tentativo non dimostra l'avviabilità del firmware.

Verifiche offline completate: parsing sintattico Python, validazione dei
due firmware reali e `git diff --check`, senza errori. Nessun ulteriore
avvio QEMU eseguito. Commit/push bloccati: `git add` fallisce con
`Unable to create '/opt/ibs-recoverywin-1.0/.git/index.lock': Read-only file system`.
File conservati nel checkout; nessuna escalation, commit o push effettuati.
