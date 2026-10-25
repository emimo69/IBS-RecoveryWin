# TEST-1.0 R3 — recovery Git, build e collaudo reale

## Stato conclusivo

- Riconciliazione e push recovery: **riusciti**, checkpoint `533cfde` verificato
  con hash remoto identico al locale.
- Build R3: **completata**, ripresa nello stesso albero isolato, exit code 0.
- ISO R3 prodotta: **sì**, originale e copia con SHA256 identico.
- Test QEMU TCG della sola Live senza dischi: **eseguito**, VM spenta alla fine.
- NAS/USB reali, WinRE, Acronis e Windows da disco: **non collaudati**.

## Recovery conservativo

Al punto iniziale la working tree era pulita. Merge-base
`036c5433ca688ab4adf30e94aad7bdba68c7466e`; commit locale `1d6f34b`
con la correzione permessi Ventoy, due commit remoti `2d10c60` e `9433078`
che aggiornano soltanto incarichi. Integrati con merge normale `533cfde`,
senza conflitti, rebase, riscrittura commit, force push o reset.
Il fix locale rimane nella storia. I tre file CODEX-TASK.md,
CODEX-AUTOSTART-TASK.md e CODEX-RECOVERY-TASK.md sono stati confrontati per blob
Git e conservati identici al remoto, senza modifiche redazionali.

Verificata assenza di processi build/VM concorrenti e circa 52 GiB disponibili.
La precedente interruzione 143 aveva lasciato polkitd parzialmente configurato,
altri cinque pacchetti e alcuni trigger pendenti. Ripresa la preparazione
live-build del medesimo chroot e completato `dpkg --configure -a` solo al suo
interno, poi ripreso `lb build`. Nessun clean/purge, cancellazione cache o nuova
build duplicata; nessun nuovo account o cambio di proprietà sul server.
La pulizia finale ha rimosso i soli mount temporanei; verificata assenza residui.

Il sandbox locale non si avviava (bwrap: impossibile creare .agents).
Le operazioni necessarie sono state eseguite tramite eccezioni esplicitamente
autorizzate per i comandi del progetto; nessuna modifica di permessi del server,
opzione Codex di bypass o configurazione del runner. Unattended non implementato.

## Artefatti conservati

Percorsi relativi a `/opt/ibs-recoverywin-1.0`.

| Campo | Valore |
| --- | --- |
| Originale generato | `.build/TEST-1.0-R3-build/IBS-RecoveryWin-TEST-1.0-R3-amd64.hybrid.iso` |
| Copia senza sovrascrittura | `IBS-RecoveryWin-TEST-1.0-R3-20261025T153110Z.iso` |
| SHA256 di entrambe | `b4e111c0ecdf164e259382d009757139b1d367d6b8afddf8038546136110c585` |
| Dimensione di ciascuna | 1656078336 byte |
| Fine build, ora server Europe/Rome | 2026-10-25 16:30:05 |
| Copia/hash verificati UTC | 2026-10-25T15:31:46.110858+00:00 |
| Commit sorgenti compilati | `533cfde5b4bda88ce1357b098270ccdb3fe81901` |

Ricontrollati gli hash delle quattro ISO precedenti (originale e copia TEST-1.0,
originale e copia R2): tutti invariati. Cache precedente conservata e riutilizzata.
Sorgenti media.py (incluso uid/gid Ventoy), vm.py, frontend, IP, launcher e unità
TeamViewer confrontati con i contenuti squashfs finali. ISO e log rimangono
locali, esclusi da GitHub.

Pacchetti verificati nel database del filesystem ISO, tutti install ok installed:
- `cifs-utils`: `2:7.4-1+deb13u2`.
- `exfatprogs`: `1.2.9-1+deb13u1`.
- `ntfs-3g`: `1:2022.10.3-5+deb13u3`.
- `openssh-server`: `1:10.0p1-7+deb13u4`.
- `ovmf`: `2025.02-8+deb13u1`.
- `python3`: `3.13.5-1`.
- `qemu-system-gui`: `1:10.0.13+ds-0+deb13u1`.
- `qemu-system-x86`: `1:10.0.13+ds-0+deb13u1`.
- `qemu-utils`: `1:10.0.13+ds-0+deb13u1`.
- `teamviewer`: `15.82.6`.
- `zenity`: `4.1.90-1`.

## Test realmente eseguiti

Passati 29 metodi unitari/statici/mock: media (7), QEMU/policy dischi (8), IP (3),
TeamViewer (8), launcher R2 (3), oltre a verify-config e preflight host.
Il test QCOW2 fittizio con qemu-img/qemu-io scrive un overlay, verifica pattern,
hash base invariato e qemu-img check; non avvia VM o dischi fisici.
La correzione Ventoy verifica opzioni ro, uid/gid admin e umask 022, oltre a
traversabilità delle cartelle runtime sotto umask privata dell'helper.

QEMU reale: TCG, 2 vCPU, 2048 MiB, sola nuova ISO come CD-ROM, nessun disco dati,
VNC localhost:5911, SSH localhost:22221. Invio alla voce Live via QMP,
nessuno screenshot. Periodo UTC `20261025T153146Z` — `2026-10-25T15:38:10.877255+00:00`.
Timeout esterno 1100 s e spegnimento nel finally; exit QEMU 0, PID
514414 verificato assente dopo il test.

| Controllo nel guest R3 | Esito |
| --- | --- |
| Login SSH con password admin/admin | riuscito |
| Servizio SSH | active |
| Locale italiano | confermato |
| teamviewerd | active/running, exit 0 |
| ibs-remote | active/exited, Result=success, exit 0 |
| TXT | file regolare leggibile da admin, root:admin 0640 |
| Launcher TeamViewer | eseguibile, checksum GVFS corretto |
| Mousepad Exec | accettato, processo presente, output soppresso |
| Sessione XFCE admin / DISPLAY / bus | presenti, attesa prima dei controlli |
| Indicatore IP | comando funzionante con indirizzo disponibile |
| IP nell'angolo alto destro e aggiornamento | configurazione top_right ed execi 2 confermate |
| Processo Conky | presente |
| Monta ISO | launcher eseguibile e attendibile |
| Avvia sistema operativo da disco | launcher eseguibile e attendibile |
| Backend capabilities | eseguito correttamente nel guest |
| QEMU e OVMF | presenti; backend rileva OVMF disponibile |
| Inventario Ventoy backend | eseguito correttamente, vuoto nel test senza dischi |
| Arresto VM e cleanup build | confermati |

## Limiti e prossimi test

L'host di sviluppo non esponeva /dev/kvm nel preflight. Il **guest** avviato
con CPU max/TCG ha invece segnalato API KVM disponibile (KVM_GET_API_VERSION=12).
Questo è un rilevamento dell'interfaccia, non prova accelerazione hardware,
prestazioni o boot WinRE/Windows. Non sono state create/avviate VM annidate.
Per quei collaudi serve un host con KVM realmente utilizzabile e un disco
virtuale di prova con un OS; la Live TCG esterna non dimostra la compatibilità.

Desktop, leggibilità visiva dell'IP, tastiera, Conky e dialoghi Zenity non sono
stati osservati graficamente. IP/cambio DHCP/wifi sono testati con fixture;
nel guest è confermata disponibilità del comando e configurazione Conky.
Monta ISO è presente e attendibile, ma NAS QNAP e Ventoy reali non sono stati
montati né sul server né nel guest. UEFI/Legacy, grafi e policy sono verificati
staticamente/mock; nessun avvio reale di WinRE, Acronis o Windows da disco.
Scrittura diretta mai eseguita. Il QCOW2 Windows 64 GB esistente non è stato usato.

Nessun ID/password TeamViewer acquisito o pubblicato. Servizi attivi non provano
una connessione remota da secondo dispositivo, ancora non collaudata.
Nessun disco fisico, altro progetto, vecchio ramo o timer modificato.
Dettagli delle funzioni e dei test in [RECOVERY-R3.md](RECOVERY-R3.md).
