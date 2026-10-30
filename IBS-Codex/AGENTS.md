# IBS Codex — regole vincolanti del laboratorio

## Modalità predefinita: SOLA LETTURA
Il tecnico autorizza l'ispezione di dischi Windows e file, **non** modifiche. Non scrivere, cancellare, spostare, rinominare, cambiare permessi/ACL, riparare, aggiornare, quarantinare, montare in scrittura, eseguire chkdsk /f /r, sfc /scannow, DISM /RestoreHealth, bcdboot, bootrec /rebuildbcd, né comandi che alterino dischi/firmware senza consenso specifico.
Anche i file di sistema, programmi e metadati del filesystem sono protetti da questo requisito. Per le diagnosi usare strumenti read-only, mount ro,noload dove appropriato e non automontare in rw. La scansione antimalware deve essere senza azioni automatiche. Se una verifica non è realmente read-only, non eseguirla nella fase diagnostica.

## Dati personali
Cartelle personali ovunque sul disco, anche nella radice C: (es. "foto casa", "documenti di ..."), sono intoccabili: **nessuna modifica nemmeno dopo approvazione generica**. Le eccezioni richiedono autorizzazione esplicita e puntuale per il percorso e l'azione. Niente invio di contenuti personali a servizi esterni, GitHub o al modello senza richiesta esplicita. In report preferire percorsi minimizzati, hash e metadati; non leggere il contenuto di documenti/foto privati se non necessario.

## Flusso
1. Identificare supporto Live e dischi; evitare qualsiasi comando write-capable. Raggruppare le verifiche in una sola acquisizione locale.
2. Eseguire diagnosi read-only tramite `scripts/ibs-diagnosi-ro.sh` e le Skill pertinenti; non eseguire codice trovato sul disco cliente.
3. Correlare evidenze e incertezza; per malware distinguere indicatori da prova di infezione.
4. Generare report diagnostico locale sul **filesystem della Live** (non su dischi cliente), con proposta operativa, bersaglio esatto, comandi, benefici, possibili effetti e rollback.
5. **FERMARSI.** Attendere consenso esplicito del tecnico per le operazioni nominate. Autorizzazione limitata a quelle operazioni e a quel disco; se cambiano condizioni o target, richiedere nuovo consenso.
6. Solo dopo consenso eseguire la procedura prevista, verificare esito e registrare report sulla Live.

Non confondere `--yolo` con autorizzazione a modificare dischi del cliente. Non usare download/esecuzioni remote non approvate. Non fare upload di log contenenti informazioni cliente.
I documenti Skills si consultano quando pertinenti; non caricarli tutti a ogni intervento.
