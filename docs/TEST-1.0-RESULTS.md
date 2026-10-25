# TEST-1.0 — prima ISO e collaudo reale del 25 ottobre 2026

## Esito

ISO compilata correttamente (live-build exit code 0). Boot in QEMU TCG
confermato tramite accesso SSH con password admin/admin. **La Live non è
ancora completamente operativa**: TeamViewer e launcher hanno problemi
residui descritti sotto. Nessuna connessione TeamViewer remota o osservazione
della GUI è stata eseguita. VM spenta a fine test, processo QEMU terminato
con exit code 0; verificata anche l'assenza del PID del test.

## Artefatti conservati nel solo progetto

Directory: `/opt/ibs-recoverywin-1.0`.

| Campo | Valore |
| --- | --- |
| ISO originale | `live-image-amd64.hybrid.iso` |
| Copia senza sovrascrittura | `IBS-RecoveryWin-TEST-1.0-20261025T131415Z.iso` |
| SHA256 di entrambe, calcolato e confrontato | `83f263a9383822a200cbcfa536e00a88216118f5ae097fa4d93c0c5b1c4a1564` |
| Dimensione di ciascuna ISO | 1549615104 byte |
| Fine build, dal log (ora server Europe/Rome) | 2026-10-25 14:12:12 |
| Copia/hash verificati (UTC) | 20261025T131415Z |
| Commit sorgenti compilato | `f1dc3677bab204390cfe095ff03b9566c49a2176` |

Il timestamp mtime dell'originale è `2026-10-25T13:00:53+00:00`:
live-build lo imposta prima della scrittura finale, non indica la fine build.
ISO originale e copia rimangono locali, escluse da GitHub. Cache conservata;
nessun `lb clean --purge` eseguito. Log locale `.build/TEST-1.0-build.log`.

Pacchetti controllati nei metadati del filesystem squashfs finale, senza mount:
- `lightdm`: `1.32.0-6+b2`, install ok installed.
- `live-config`: `11.0.5`, install ok installed.
- `live-config-systemd`: `11.0.5`, install ok installed.
- `openssh-server`: `1:10.0p1-7+deb13u4`, install ok installed.
- `teamviewer`: `15.82.6`, install ok installed.
- `user-setup`: `1.107`, install ok installed.

## Controlli prima della compilazione

Passati: `sh scripts/verify-config.sh`, `python3 scripts/verify-remote.py`,
`python3 scripts/test-remote.py` (7 metodi con sottocasi) e
`python3 scripts/preflight-live.py --host`. Sono controlli statici e test con
CLI simulata: non provano da soli servizi, GUI o connessione TeamViewer.
Conservati admin/admin, configurazione italiana, SSH, autostart e percorso TXT.
Il TXT pronto contiene soltanto ID, password e IP. Nessuna credenziale
TeamViewer reale è stata letta o acquisita nei risultati.

Prima della build salvato e verificato su GitHub il commit `f1dc367`.
L'hook TeamViewer ha scaricato e installato 15.82.6 senza errori bloccanti;
la presenza nell'ISO è stata controllata separatamente dopo la build.
Non sono state necessarie altre correzioni sorgenti di boot/build.

## Test QEMU effettivo

Processo eseguito come utente server già esistente `utente`, senza modificare
proprietà dei file o creare account server. TCG, CPU max, 2 vCPU, RAM 2048 MiB,
solo ISO CD-ROM; nessun disco dati o passthrough. VNC su localhost:5911,
SSH inoltrato solo da localhost:22221. Monitor QMP locale per controllo e arresto.
Nessun QCOW2 collegato, nessuna VM annidata, nessun firmware host modificato.
Il QCOW2 Windows esterno non è stato aperto né modificato.

Il menu ISO usa `timeout 0`: attende la scelta dell'utente. Selezionata la voce
predefinita **Live system (amd64)** con un solo Invio tramite QMP.
Non confondere questa selezione con il login automatico XFCE.
Il processo era limitato a 900 s complessivi; attesa SSH fino a 600 s e
servizio di assistenza fino a ulteriori 180 s. Nessuna schermata è stata
acquisita per evitare di esporre ID/password.

Periodo del processo: `20261025T131630Z` — `2026-10-25T13:24:32.902682+00:00`.

| Verifica reale | Risultato |
| --- | --- |
| Boot fino a sessione SSH | confermato |
| Autenticazione SSH con password admin/admin | riuscita |
| `id -un` | admin |
| Lingua `LANG` | it_IT.UTF-8 |
| Servizio SSH | active |
| Processo xfce4-session | presente, GUI non osservata |
| TXT leggibile da admin senza sudo | sì |
| TXT non vuoto | sì, contenuto non letto |
| Proprietario e permessi TXT | root:admin 640 |
| Servizio teamviewerd | inactive |
| Servizio ibs-remote | failed, Result=exit-code, ExecMainStatus=1 |
| Launcher nella cartella risolta da xdg-user-dir DESKTOP | test eseguibile fallito |
| Arresto finale | QEMU terminato, exit code 0, PID assente |

## Problemi residui e limiti

1. TeamViewer **non operativo nel controllo effettuato**: daemon inattivo e
   servizio di preparazione fallito. La presenza del pacchetto nell'ISO non
   equivale al funzionamento. Non è stata determinata la causa; non sono stati
   letti journal/CLI potenzialmente contenenti ID o password.
2. Il controllo del launcher ha restituito “non eseguibile”. Non è stato
   distinto un errore di creazione da percorso/localizzazione o ritardo
   dell'autostart: l'icona e l'attendibilità devono essere verificate nel desktop.
3. TXT presente e leggibile non significa credenziali pronte: ibs-remote è
   fallito. ID/password reali non verificati, nessun accesso remoto TeamViewer.
4. XFCE è in esecuzione ma GUI, login automatico visivo, tastiera italiana,
   icona, Mousepad e Conky non sono stati osservati. Nessun test di riavvio.
5. /dev/kvm e vmx/svm assenti: non disponibile accelerazione KVM nel server
   attuale. Il test usa TCG e non dimostra prestazioni su hardware reale.

Il task watcher è stato lasciato invariato. Nessun disco fisico, altro progetto
o vecchio ramo è stato modificato. Non sono state cancellate ISO precedenti.
I dati pubblicati riportano solo metadati ISO ed esiti, senza segreti.
