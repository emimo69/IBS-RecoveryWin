# Controllo incarichi GitHub — predisposto, non attivato

Solo Debian di sviluppo, /opt/ibs-recoverywin-1.0, ramo ibs-recoverywin-1.0.
Non è incluso nella Live. Nessuna installazione o attivazione eseguita.

La modalità scelta è **assistita**: il timer controlla ogni due minuti il blob
CODEX-TASK.md del repository HTTPS fisso emimo69/IBS-RecoveryWin. Non può
certificare che l'autore sia ChatGPT: ogni nuovo incarico va revisionato.
Il controllo aggiorna il checkout solo tramite fast-forward e solo se pulito,
memorizza il blob in `.task-watch/pending` e lascia un messaggio in `status`.
Non esegue autonomamente le istruzioni del task.

`flock` copre fetch, aggiornamento, stato e sessione assistita. Anche altri
strumenti di modifica devono essere fermati durante il controllo: il lock non
coordina editor o sessioni Codex esterne. Git divergente, modifiche locali o
errori bloccano il controllo; nessun reset o cancellazione automatica.
Il fetch usa HTTPS fisso, non stampa output e non interroga file credenziali.
Git può usare l'autenticazione già configurata; nessun token viene configurato.
Timeout rete: 60 secondi. Stato/log hanno umask 0077 e sono esclusi da Git.

## Installazione futura, solo dopo verifica

Come utente di sviluppo non root, proprietario del checkout e con Git/Codex
configurati: `./automation/install`. Installa unità **utente**, senza avviarle.
Questa installazione scrive ~/.config/systemd/user e richiede autorizzazione
nel nostro ambiente ristretto; non è stata eseguita in questo incarico.
Prima controllare i task esistenti e segnare quello già svolto:

```
./automation/task-watch poll
./automation/task-watch complete HASH_BLOB_REVISIONATO
```

`complete` richiede checkout pulito, HEAD uguale al remoto e hash corrente
identico a quello indicato. Va usato solo dopo verifiche e push riusciti.
Un exit code 0 di Codex non viene scambiato per task completato.
I marker `completed/HASH` persistono: nuovi commit con lo stesso task non lo
rilanciano, anche se il task viene ripristinato successivamente.

Dopo autorizzazione separata: `systemctl --user enable --now ibs-task-watch.timer`.
Non è fornito un comando di attivazione automatica nello script install.
Serve una sessione systemd utente attiva; non abilitiamo linger.
Consultare `.task-watch/status` e `.task-watch/logs/`.
Per eseguire un task revisionato: `./automation/task-watch assist` da terminale.
Al termine controllare risultato, test e push, poi usare `complete HASH`.
Su errore, correggere manualmente e dare `./automation/task-watch retry`.
Per fermare e disabilitare: `./automation/disable`; stato e log sono conservati.

## Permessi e Codex

La CLI locale supporta `codex exec --sandbox workspace-write -C DIR` per
esecuzioni non interattive. La [documentazione ufficiale OpenAI](https://learn.chatgpt.com/docs/non-interactive-mode)
descrive sandbox e permessi. Non abilitiamo tale invocazione nel timer:
commit/push e altre operazioni possono richiedere approvazioni non gestibili
in una sessione senza terminale. La modalità assistita usa `codex` interattivo,
`--ask-for-approval on-request`, `--sandbox workspace-write` e `-C` fisso.
Nessuna approvazione automatica, opzione di bypass o sandbox disabilitata.
La directory di lavoro e sandbox limitano le scritture; non costituiscono
una garanzia di isolamento di tutte le letture. Non eseguiamo task arbitrari
non revisionati. Non si registrano stdout/stderr di Codex: potrebbero contenere
segreti. Solo log di controllo, hash e risultato/exit code sono persistiti.
Il runner non legge /mnt/teamviewer.txt né file di autenticazione.

## Verifiche eseguite e limiti

`python3 scripts/verify-task-watch.py` controlla staticamente timer, lock,
stato/deduplicazione, modalità assistita, permessi e assenza di attivazione.
`./scripts/verify-config.sh` verifica i sorgenti Live. Non vengono eseguiti
fetch tramite runner, installazione, timer, Codex figlio, build o boot.
Non è provato il funzionamento reale del servizio o della Live.

Analisi Live: i sorgenti impostano admin/admin, autologin LightDM, abilitazione
SSH nel chroot e generazione chiavi al boot. TeamViewer usa /mnt/teamviewer.txt,
pubblicazione atomica root:admin 0640 e launcher Mousepad nella sessione XFCE.
Difetto rilevato, lasciato invariato perché fuori incarico: il parser ID nello
script ibs-remote accetta un prefisso numerico seguito da testo e la pipeline
non conserva l'exit code di `teamviewer info`; andrebbe irrigidito prima del
collaudo. Inoltre i messaggi di errore imprevisto possono restare su
“inizializzazione in corso”, perché manca una gestione EXIT generale.
Non deduciamo dai soli sorgenti che SSH o TeamViewer siano operativi.
