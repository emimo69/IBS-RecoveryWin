# IBS-RecoveryWin — prova autonoma del timer (incarico di sola lettura)

**Obiettivo:** verificare che `ibs-task-watch.timer` avvii Codex da solo, senza richieste Yes, dopo aver rilevato questo nuovo blob di `CODEX-TASK.md`. Incarico innocuo, breve, conclusivo.

1. Leggi `AGENTS.md`, il presente incarico e `docs/TEST-1.0-R3-RESULTS.md` se presente. Controlla senza modificare nulla che la build R3 abbia un rapporto di collaudo e che il repository sia sul ramo `ibs-recoverywin-1.0`.
2. Verifica in sola lettura `scripts/verify-config.sh` o gli script di verifica equivalenti. Riferisci nel riepilogo sintetico solo ciò che puoi dimostrare.
3. **NON modificare file, NON eseguire commit o push**: il nuovo incarico stesso è già stato pubblicato su GitHub; un controllo senza modifiche non richiede ulteriori commit. Non eseguire build, QEMU, installazioni, comandi root o accessi a dischi fisici, USB/NAS, credenziali o TeamViewer.
4. Termina con esito positivo se i controlli di sola lettura sono coerenti. Se la sandbox impedisce una verifica, riportalo senza tentare escalation o creare modifiche. Non modificare `CODEX-TASK.md`.
5. Il sistema automatico dovrà verificare separatamente HEAD locale/remoto, working tree pulita e test di configurazione prima di contrassegnare il task `success`. Non avviare un'altra sessione Codex.

**Priorità successiva, DOPO che questo incarico ha stato success verificato:** iniziare con test funzionali QEMU/WinRE su macchina con KVM e accesso sicuro; mai dichiararli riusciti senza prove reali. Questo punto è solo un promemoria e non va eseguito durante il test del timer.
