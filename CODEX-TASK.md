# PRIORITÀ ASSOLUTA — riparazione timer automatico Codex

Leggi AGENTS.md e svolgi questo incarico PRIMA di R4/QEMU. Non toccare ISO R2/R3, dischi fisici, altri progetti, credenziali, SSH o TeamViewer.

SITUAZIONE CONFERMATA: il timer systemd --user ibs-task-watch.timer controlla GitHub ogni 2 minuti, unattended è abilitato. I nuovi incarichi sono rilevati, ma Codex non interattivo termina con exit_code 1. Git locale e remoto erano sincronizzati e puliti; il vecchio runner registra 'verifica_git', poi 'hash_non_ripetibile'. Il servizio ha ProtectSystem=strict, ProtectHome=read-only, NoNewPrivileges=true, PrivateTmp=true; in passato Codex workspace-write ha dato errori bubblewrap. Non è ancora dimostrata la causa di exit 1.

1. Studia davvero automation/unattended.py, automation/task-watch, automation/systemd/ibs-task-watch.service, automation/enable, gli script test e i record .task-watch. Distingui problemi delle restrizioni systemd da quelli della sandbox Codex, della quota, dell'autenticazione e del prompt. Non tirare a indovinare.
2. Verifica con un prompt innocuo 'Rispondi OK' in una prova senza modifica di file, prima come utente utente e poi sotto il servizio systemd. Raccogli solo codice uscita e categoria di errore senza registrare output privati, token o credenziali.
3. Correggi la causa effettiva con privilegi minimi, senza bypassare la sandbox o usare dangerous flags. Mantieni lock, no doppie sessioni, deduplicazione per hash e blocco retry infiniti. Un task fallito può essere riprovato soltanto con una modalità esplicita e controllata.
4. Test di regressione e verifiche Git, commit e push ove consentiti. Se la sandbox vieta Git o systemd, conserva le patch, spiega l'ostacolo e indica un solo comando host strettamente necessario. Non aggirare i permessi.
5. Esegui un collaudo end-to-end con incarico fittizio e non distruttivo: timer avvia Codex senza Yes e verifica prima running e poi success. Se questo non è possibile, non dichiarare timer funzionante.
6. SOLO DOPO la riparazione riprendi R4 su QEMU/WinRE, senza avviare VM su dischi fisici né alterare ISO precedenti.

Procedi senza richiedere continue conferme, nei limiti dei permessi disponibili.
