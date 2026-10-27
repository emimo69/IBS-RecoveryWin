# Requisiti approvati per IBS-RecoveryWin 2.0

- Nuovo progetto in /opt/ibs-recoverywin-2.0; versione 1.0 invariata.
- Debian Trixie amd64, XFCE in italiano e login automatico.
- SSH attivo; utente admin e password admin, entrambi minuscoli.
- TeamViewer Host installato e automatico al boot; ID e password in /mnt/teamviewer.txt.
- Editor TXT e copia/incolla nel terminale.
- QEMU per WinRE; sorgente QNAP /mnt/ibs-iso/ISO/IBS-WinRE.iso, incorporata nella live.
- Copia/incolla testo anche tra Debian e WinRE.
- Dischi fisici selezionabili in lettura e scrittura dentro WinRE, autorizzati dall’utente il 27 ottobre 2026. Esclusi dischi montati, swap e supporto live; niente smontaggi automatici.
- Prove di sviluppo solo su dischi virtuali basati su file, senza modificare dischi reali.
- Compilazione delle ISO autorizzata esplicitamente dall’utente il 27 ottobre 2026 con la richiesta di compilare la 2.0.
- Commit e push GitHub a modifica completata, con verifica del riferimento remoto.
