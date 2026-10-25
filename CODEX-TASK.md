# Incarico Codex — IBS-RecoveryWin 1.0

Leggi `AGENTS.md` e applica questa correzione **solo** nel ramo `ibs-recoverywin-1.0`.

1. Il file di assistenza deve essere esattamente `/mnt/teamviewer.txt`, non `/run/ibs/teamviewer.txt`. Controlla e aggiorna tutti i riferimenti (script, Conky, documentazione e servizi).
2. Il file deve essere creato automaticamente all'avvio con TeamViewer ID reale, password effettivamente impostata nella sessione corrente e indirizzo IP locale. Se non è pronto, mostra un messaggio comprensibile senza presentare credenziali errate.
3. L'utente `admin` deve poter leggere `/mnt/teamviewer.txt` senza sudo.
4. Crea sul desktop XFCE dell'utente admin un launcher `TeamViewer ID e Password` che apra `/mnt/teamviewer.txt` con Mousepad. Assicurati che sia eseguibile e attendibile nel desktop XFCE.
5. Mantieni funzionanti login `admin/admin`, SSH e il resto della Live; non introdurre cambiamenti non richiesti.
6. Verifica staticamente i percorsi, i permessi previsti e la sintassi degli script. Non affermare che TeamViewer funziona realmente senza collaudo.
7. Esegui commit e push su GitHub sul ramo `ibs-recoverywin-1.0`, conferma l'hash remoto uguale all'hash locale e riporta i file modificati.

**Non compilare la ISO. Non toccare dischi fisici, altri progetti o i vecchi rami.**
