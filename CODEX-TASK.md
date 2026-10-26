# IBS-RecoveryWin R4C — convalida post-fix OVMF e chiusura rapporto

Leggi AGENTS.md. L'ultimo commit su ibs-recoverywin-1.0 ha pubblicato la correzione OVMF in vm.py e un nuovo test in scripts/test-vm.py (9 test VM + 7 test media passati nella shell host). R2/R3 sono basi stabili da non modificare. Non ripetere la patch R4B-proposed.patch; non applicarla una seconda volta.

1. Verifica il codice corrente realmente presente su GitHub e nella checkout locale: l'escaping delle virgole nei valori file= dei due -drive OVMF e il nuovo test senza cancellare alcun test originale. Esegui python3 -B scripts/test-vm.py, python3 -B scripts/test-media.py e bash scripts/verify-config.sh se possibile. Registra risultati reali, senza inventarli.
2. Verifica staticamente la gestione dei percorsi e i messaggi d'errore delle azioni Monta ISO e Avvia OS, NAS/Ventoy/ISO WinRE/Acronis, con fixture e mock senza collegare dischi, NAS o USB veri. Se trovi un difetto concreto, proponi correzione minima e relativo test. Non attivare modalità diretta su dischi reali.
3. Aggiorna il rapporto R4-PROGRESS.md: ora è obsoleto perché dice 'BLOCCATO' anche se la patch OVMF e il test sono stati pubblicati e superati. Usa però la dicitura corretta 'R4B validata nei test statici; avvio reale WinRE/Windows e NAS/USB non collaudati'. Documenta fedelmente test, limiti e prossimi passi.
4. Commit/push delle modifiche comprovate e rapporto aggiornato. Se la sandbox non permette scrittura di .git, NON ripetere procedure fallite né rimuovere permessi: salva una patch piccola o un rapporto locale fuori dai sorgenti, segnala con precisione che il commit richiede la shell host; non dichiarare concluso senza prove.
5. Non modificare timer, servizio systemd, CODEX-TASK.md, ISO R2/R3, cache o altri progetti. Nessuna build ISO e nessuna VM con dischi fisici senza autorizzazione specifica. La sandbox e i limiti di protezione devono restare attivi.

Obiettivo: chiudere bene R4 e preparare un successivo test sicuro di WinRE, SENZA attribuire al runner 'success' un collaudo funzionale inesistente.
