# Runner incarichi GitHub

Solo `/opt/ibs-recoverywin-1.0`, ramo `ibs-recoverywin-1.0`, utente non root.
Non incluso nella Live. Nessuna build ISO, modifica a dischi o VM.

Il timer ha periodo di due minuti dopo la fine del servizio. Un controllo non
crea una sessione: senza `.task-watch/unattended-enabled` resta in poll.
Il fetch usa un repository bare separato in `.task-watch/monitor.git`; il poll
non fa checkout o merge nella working tree. Il blob di CODEX-TASK.md identifica
l'incarico, indipendentemente dai commit successivi. Non viene autenticata
l'identità dell'autore del task: il ramo remoto deve essere fidato.

`flock` è condiviso con la modalità assistita e resta acquisito per tutta la
sessione, anche nei processi figli. Ogni processo con nome contenente Codex
blocca l'avvio automatico; in un namespace senza visibilità dell'host non si
può certificare l'assenza di altre sessioni. Editor esterni e nuovi Codex
interattivi non rispettano il lock: non avviarli mentre lavora il runner.

La modalità unattended usa la sintassi verificata nella CLI installata:
`codex --ask-for-approval never exec --sandbox workspace-write -C DIR --json`.
Nessun bypass o ampliamento automatico dei permessi. Timeout sessione due ore,
TERM al gruppo dei processi, poi KILL dopo dieci secondi. systemd applica anche
KillMode=control-group e TimeoutStopSec=20. Le build eventualmente autorizzate
nel task restano soggette al timeout.

Stati atomici privati in `.task-watch/runs/HASH.json`: running, success, failed,
quota_in_attesa, con hash task, commit iniziale e codice uscita. Un running
residuo diventa failed al riavvio. Success e failed non vengono rilanciati
automaticamente; conservare questi file. I vecchi marker completed sono
rispettati. Exit zero richiede anche verify-config.sh riuscito, checkout pulito,
HEAD identico al ramo remoto e task invariato. verify-config è un controllo
statico: i test specifici del task devono essere eseguiti dal Codex figlio;
questo runner non certifica funzionamento Live, SSH o TeamViewer.

Gli errori quota riconoscibili negli eventi JSON di errore impostano una pausa
di sei ore (intervallo locale, NON timestamp ufficiale di reset). Il timer resta
attivo senza creare sessioni ogni due minuti. Riprende lo stesso blob prima di
nuovi task e conserva le modifiche parziali per la ripresa. Se la CLI non espone
un errore quota riconoscibile, lo stato è failed e richiede diagnosi manuale.
Nessun processo può superare la quota Codex. Non si salva il transcript della
CLI né output Git: solo stati, hash e codici; non si leggono file TeamViewer.

## Comandi

- Test senza Codex reale o rete: `python3 scripts/test-unattended.py`.
- Verifiche statiche: `python3 scripts/verify-task-watch.py` e `./scripts/verify-config.sh`.
- Poll singolo: `./automation/task-watch poll`.
- Stato: `./automation/status` (include ultimo controllo, hash e attesa quota).
- Fallback interattivo: `./automation/task-watch assist`; resta soggetto a checkout pulito e al precedente blocco manuale.
- Arresto immediato: `./automation/disable` (rimuove prima l'abilitazione unattended).

Dopo commit/push verificato, dalla shell host e dopo la chiusura di tutte le
sessioni Codex: `./automation/enable`. Il comando verifica bus, processi,
checkout e remoto, riesegue i test e lancia uno smoke test Codex reale innocuo,
con prompt distinto dal task di produzione e senza strumenti. Solo se riesce
installa le unità utente e abilita il timer. `automation/install` da solo
installa senza attivare; non configura linger. Non lanciare enable mentre R3
lavora. Le unità già installate non vengono aggiornate dalla modifica dei file
nel repository.

## Consegna del 25 ottobre 2026: attivazione bloccata

Superati 13 test offline, incluso un vero processo fittizio terminato per
timeout, e i controlli statici Live/shell. Nessun Codex figlio reale avviato.
Da questa sessione il bus utente restituisce Operation not permitted, anche se
funziona nella shell host. Anche systemd-analyze --user verify è bloccato da
SO_PASSCRED. La visibilità processi è limitata e PID 1 è Codex: non è possibile
certificare assenza di sessioni attive. Nessuna configurazione systemd attiva è
stata cambiata; lo smoke reale e l'attivazione restano da eseguire sull'host.

La sandbox corrente protegge `.git` in sola lettura e limita la rete. Questi
limiti possono impedire commit/push anche al runner non interattivo: in tal
caso il task diventa failed/incompleto, senza escalation o retry continuo.
Per automazione completa serve un'integrazione Git approvata e limitata a
questo repository/ramo, con verifica di diff e destinazione, non accesso
generale o sandbox disabilitata. Tale integrazione non è implementata qui.
La documentazione ufficiale conferma i percorsi Git protetti:
https://learn.chatgpt.com/docs/agent-approvals-security
