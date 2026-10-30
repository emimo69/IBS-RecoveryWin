# IBS Codex — Diagnostica Windows

Repository di procedure condivise, separato dalle ISO. Modalità iniziale: **analisi soltanto**, anche per C:, programmi e file Windows. Le riparazioni sono *proposte*, non avviate prima dell'autorizzazione del tecnico.

## Uso sulla Debian Live
Clonare il ramo in una directory di lavoro separata; lanciare `bash scripts/ibs-diagnosi-ro.sh` per acquisire informazioni hardware/dischi in sola lettura e un report locale. Leggere `AGENTS.md` e la Skill pertinente, quindi interpretare il report. Per analisi offline di file Windows o sospetto malware, individuare l'installazione e proporre strumenti adatti, mantenendo i volumi cliente non montati in scrittura.

## Ambito
SMART/SATA/NVMe, partizioni GPT/MBR, boot UEFI, NTFS, log, BSOD e triage antivirus. Nessuna cancellazione automatica, quarantena, disinfezione o riparazione automatica.

## Casi risolti
Documentare solo dopo verifica reale e con dati dei clienti anonimizzati. Ogni nuova procedura richiede revisione prima della pubblicazione.
