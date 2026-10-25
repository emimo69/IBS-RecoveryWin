# TEST-1.0 R2 — diagnosi, correzione e nuovo test reale

## Esito

Una sola nuova ISO compilata dopo diagnosi sulla ISO precedente. Nella R2
**teamviewerd è active/running e ibs-remote è active/exited, Result=success,
ExecMainStatus=0**. SSH admin/admin, italiano, file TXT e launcher verificati
nel guest. Non è stata provata una connessione TeamViewer da un altro dispositivo.

## Cause e correzioni accertate

Il daemon della prima ISO funziona quando avviato separatamente. Il codice
vendor 15.82.6 arresta/riavvia il daemon durante `teamviewer passwd`, oltre al
restart previsto dalla prima configurazione licenza. Il nostro Requires
propagava lo stop a ibs-remote. Unica correzione funzionale: **Requires→Wants**,
con After conservato. Il nuovo filesystem squashfs contiene esattamente
l'unità corretta dei sorgenti. Il test R2 conferma che i restart del daemon
non interrompono più IBS. Nessuna modifica ad admin/admin o SSH.

Il launcher **non richiedeva una correzione**: il primo controllo era prematuro.
Due diagnosi sulla ISO originale hanno distinto SSH pronto da XFCE/autostart
pronti. Attendendo XFCE, la stessa vecchia ISO aveva già il launcher eseguibile
in Scrivania; il probe nel bus grafico terminava con exit code 0. Conservato
il launcher funzionante e corretto il test per attendere davvero la sessione.
Dettagli e strumento ripetibile in [DIAG-TEST-1.0.md](DIAG-TEST-1.0.md).

## Nuova ISO conservata

Tutti i percorsi seguenti sono relativi a `/opt/ibs-recoverywin-1.0`.

| Campo | Valore |
| --- | --- |
| ISO prodotta nell'albero isolato | `.build/TEST-1.0-R2-build/IBS-RecoveryWin-TEST-1.0-R2-amd64.hybrid.iso` |
| Copia nel progetto, creata senza sovrascrivere | `IBS-RecoveryWin-TEST-1.0-R2-amd64.hybrid.iso` |
| SHA256 di entrambe | `c1c8a6bb8915e2df50fd754202032be4b30b55fd8de8a790b04648a5156c9d34` |
| Dimensione di ciascuna | 1549615104 byte |
| Fine build (ora server Europe/Rome) | 2026-10-25 14:58:07 |
| Copia/hash verificati UTC | 2026-10-25T13:59:13.792569+00:00 |
| Commit dei sorgenti prima della build | `0800b163749a36c743c1f8c229b9eb9a60ffe37a` |
| Pacchetto TeamViewer verificato nel squashfs | 15.82.6, install ok installed |
| Exit code live-build | 0 |

Vecchia ISO `live-image-amd64.hybrid.iso` e copia
`IBS-RecoveryWin-TEST-1.0-20261025T131415Z.iso` preservate integralmente:
ricontrollato SHA256 di entrambe, ancora
`83f263a9383822a200cbcfa536e00a88216118f5ae097fa4d93c0c5b1c4a1564`.
Nessuna pulizia, nessun clean --purge; cache condivisa tramite collegamento
nell'albero di build isolato. Nessuna ISO o cache committata.

## Confronto del test reale

QEMU TCG come utente server esistente utente, 2 vCPU, 2048 MiB, sola ISO CD-ROM,
nessun disco virtuale/fisico, VNC localhost:5911 e SSH localhost:22221.
Selezione della Live predefinita con Invio via QMP, senza screenshot.
Intervallo UTC: `20261025T135913Z` — `2026-10-25T14:04:55.381905+00:00`.
Timeout esterno 1100 s con spegnimento nel finally; VM terminata con exit code
0 e PID 420400 verificato assente dopo il test.

| Controllo | Primo test | R2 |
| --- | --- | --- |
| SSH password admin/admin | riuscito | riuscito |
| SSH servizio | active | active |
| Locale italiano | confermato | confermato |
| teamviewerd | inactive | active/running, exit 0 |
| ibs-remote | failed, exit 1 | active/exited, Result=success, exit 0 |
| TXT leggibile da admin senza sudo | sì | sì, file regolare root:admin 0640 |
| Sessione XFCE admin con DISPLAY/bus | attesa non verificata | presente, attesa prima del controllo |
| Launcher in Scrivania | falso negativo prematuro | presente ed eseguibile già prima del probe |
| Checksum GVFS confrontato con SHA256 launcher | non verificato | corrisponde, attendibile per XFCE |
| Exec del launcher | non provato | percorso corretto; Mousepad avviato, processo presente |
| Connessione TeamViewer esterna | non provata | non provata |

Il probe Mousepad avvia soltanto l'Exec richiesto nella sessione del guest,
con stdout/stderr soppressi. Nessuno screenshot, nessuna lettura o acquisizione
del contenuto TXT da parte della diagnosi. Il processo presente conferma l'avvio
dell'app, non l'osservazione visiva del documento o dell'intera GUI.

## Verifiche automatiche, tracciabilità e limiti

Passati 8 test TeamViewer con sottocasi, 3 test launcher isolati con HOME/XDG/GVFS
simulati, preflight e verifiche statiche/sintassi. Nuovo runner
`scripts/test-live-qemu.py` con attesa XFCE e stato del servizio, diagnosi
guest-only filtrata, timeout e spegnimento. Il codice del probe Mousepad è
stato inoltre eseguito realmente nel guest R2; nessun transcript di credenziali.

Commit sorgenti/fix: `20c61ca` e `0800b16`, ciascuno pubblicato e confrontato con
l'hash remoto prima di procedere. La sola ulteriore modifica allo strumento
diagnostico dopo la build prova Mousepad; non modifica i contenuti della ISO.

Restano da collaudare visivamente desktop, Conky, tastiera e apertura documento;
non verificati accesso remoto TeamViewer da secondo dispositivo e riavvio.
ID/password reali non sono stati letti, registrati o pubblicati. Servizi attivi
non equivalgono a prova di connessione remota o validazione esterna della password.
Il task watcher è invariato. Nessun QCOW2 Windows, disco fisico, altro progetto,
vecchio ramo, account o proprietà di cartelle preesistenti del server modificato.
