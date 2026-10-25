# Codex — Attivazione esecuzione automatica incarichi GitHub

Questo incarico è **separato** dall'attuale CODEX-TASK.md (fase R3): NON interrompere o sostituire R3. Eseguilo soltanto quando l'utente richiede di leggere CODEX-AUTOSTART-TASK.md o quando R3 è terminata e viene espressamente richiamato.

## Scopo
La Debian di sviluppo esegue già ogni due minuti il timer systemd --user ibs-task-watch.timer, che oggi scarica i nuovi CODEX-TASK.md ma NON esegue Codex. Evolvilo in un runner non interattivo, senza dover premere Yes. Mantieni possibilità di disattivare e modalità assistita come fallback.

## Requisiti obbligatori
1. Prima verifica, tramite `codex exec --help`, le opzioni effettivamente supportate dalla CLI installata. Usa soltanto opzioni confermate. Esecuzione in sandbox workspace-write e autorizzazioni non interattive: non usare bypass/sandbox disabilitata, non eseguire come root.
2. Implementa una modalità unattended separata e testabile che avvii Codex su un nuovo task SOLO se il timer rileva un hash blob CODEX-TASK.md non ancora eseguito. Mantieni `flock` a copertura di tutta la sessione; timeout e segnali di terminazione adeguati. Escludi sovrapposizioni con la sessione Codex già aperta, chiedendo di chiuderla prima di abilitare il nuovo servizio.
3. Non permettere esecuzione ripetuta dello stesso hash. Registra marcatori distinti `running`, `success`, `failed`, con codice di uscita, commit di ingresso e hash task. Un exit 0 della CLI non dimostra che push remoto o test siano riusciti: verifica sempre stato Git e hash del ramo remoto, e che non esistano cambiamenti non salvati; se qualcosa manca, segnala stato incompleto e blocca retry automatico.
4. Il servizio deve poter raggiungere GitHub per fetch/push se le autorizzazioni della sandbox lo permettono; se non lo consentono, NON aggirare la sandbox. Segnala chiaramente il limite e proponi un'integrazione approvata per le sole operazioni Git, anziché interrompere il lavoro o concedere accesso generale.
5. Nessun comando in background deve modificare dischi fisici, riavviare host, cancellare ISO vecchie, cambiare altri progetti o utenti. La nuova funzione può eseguire soltanto incarichi software sul progetto autorizzato. I task R3 possono autorizzare una build e test virtuali senza dischi, ma non una VM che accede a dischi reali.
6. Impedisci che un nuovo CODEX-TASK.md pubblicato mentre Codex lavora annulli il lavoro corrente. Quando finisce, controlla nuovi task al successivo tick; non interrompere mai una compilazione in corso salvo timeout/errori seri.
7. Mantieni log diagnostici senza contenuti TeamViewer ID/password o token. Aggiungi comandi brevi per vedere stato, abilitare/disabilitare e testare con mock Codex/Git, senza invocare Codex reale.
8. NESSUNA attivazione immediata: prepara patch, test e documentazione, commit e push. Chiedi esplicita conferma solo per l'ATTIVAZIONE IN PRODUZIONE del nuovo runner dopo la revisione. Il timer attuale deve continuare a funzionare.
9. Conserva tutte le funzionalità Live/TeamViewer/SSH e non cambiare Codex-TASK.md attuale.
