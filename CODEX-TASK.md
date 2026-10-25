# CODEX-TASK.md — INCARICO ATTUALE: prima ISO e test QEMU della Live 1.0

**ESEGUI QUESTO INCARICO**, non limitarti a leggerlo. Leggi AGENTS.md. Il proprietario del progetto ha autorizzato esplicitamente la **prima compilazione della nuova ISO** e i **test in QEMU senza dischi fisici**. Questa autorizzazione vale soltanto per il progetto `/opt/ibs-recoverywin-1.0` sul ramo `ibs-recoverywin-1.0`. I precedenti incarichi sono conclusi.

## 1. Verifiche e salvataggio preventivo
- Recupera l'ultima versione del ramo GitHub; non sovrascrivere modifiche locali. Verifica stato Git.
- Esegui i controlli statici: `scripts/verify-config.sh`, `scripts/verify-remote.py`, `scripts/test-remote.py`, `scripts/preflight-live.py --host`, usando gli interpreti appropriati e segnalando i limiti delle verifiche.
- Verifica che `/mnt/teamviewer.txt` resti SOLO un semplice file TXT con ID reale e password reale della sessione; evita dettagli diagnostici superflui nel TXT. Conserva admin/admin, SSH, icona XFCE Mousepad, italiano.
- Correggi solo errori reali necessari al boot o alla build, con commit e push **prima della compilazione**. Non cambiare funzionalità già verificate né la modalità operativa del timer.

## 2. Prima compilazione
- Costruisci una ISO Debian Trixie XFCE da `/opt/ibs-recoverywin-1.0` tramite live-build esistente. Non eseguire `lb clean --purge`; mantieni cache pacchetti. Non toccare progetti precedenti.
- Se il download TeamViewer o dipendenze fallisce, fermati con diagnostica precisa. Non dichiarare riuscita la build se manca TeamViewer.
- Conserva la ISO originale generata e una copia con nome versione TEST-1.0 nel percorso del solo nuovo progetto, senza sovrascrivere file esistenti. File ISO non vanno su GitHub.
- Registra in un file di documentazione GitHub il nome, SHA256, dimensione e data della ISO prodotta, senza segreti.

## 3. Test virtuale SENZA dischi
- Se esiste QEMU, avvia solo la Live con emulazione TCG: il server attuale non ha /dev/kvm. Nessun disco QCOW2, /dev/sd*, /dev/nvme*, passthrough, o modifica firmware host.
- Usa un metodo osservabile compatibile con server senza display (QEMU headless + VNC locale/seriale se disponibile), con limiti e timeout; lascia la VM spenta alla fine. Evita VM annidate, non usare il QCOW2 Windows da 64 GB in questo test.
- Verifica effettivamente quanto possibile: boot, SSH via port forwarding localhost, user admin/admin, servizio TeamViewer, disponibilità di /mnt/teamviewer.txt. **Non dichiarare testata la GUI o la connessione TeamViewer da remoto se non puoi osservarle davvero**. Se TCG non completa il boot, riporta lo stato concreto e fermati senza simulare successo.
- Non leggere, stampare, registrare su GitHub ID/password reali TeamViewer.

## 4. Tracciabilità e conclusione
- Dopo le modifiche sorgenti, fai commit e push frequenti sul ramo `ibs-recoverywin-1.0`, verificando hash remoto=locale. Pubblica risultati/limitazioni test in documentazione con ulteriore commit e push.
- Mai cancellare o riscrivere dischi fisici. Non modificare vecchi progetti/rami; non cambiare proprietà file del server né creare nuovi account sul server.
- Mantieni il task watcher operativo e invariato. Non abilitare esecuzione incontrollata o bypass delle approvazioni.
- Alla fine riporta commit, nome ISO e risultati REALI, con problemi residui separati.

**Autorizzata la build della nuova Live e la prova QEMU SENZA dischi. NON è autorizzato modificare dischi fisici, usare il QCOW2 Windows, cancellare le ISO vecchie o intervenire su progetti diversi.**
