# Diagnosi timer — 26 ottobre 2026

Incarico letto direttamente su GitHub, ramo ibs-recoverywin-1.0,
CODEX-TASK.md blob `3254ed66f041682721275efbb6335a0c15e29252`.
R4 abbandonata; nessuna modifica a QEMU, WinRE, ISO, SSH o TeamViewer.

## Prove osservate

- I due record falliti più recenti conservano exit 1 e
  `codex_sandbox_permessi`. Quelli precedenti riportano `verifica_git`:
  questa vecchia etichetta non dimostra un errore Git.
- Il runner corrente segnala `poll_codex_attivo`: questa sessione interattiva
  è aperta. Nessun marker storico è stato rimosso o riarmato.
- CLI installata 0.164.0; sintassi verificata con exec --help.
- Smoke innocuo come UID 1000 **dentro la sandbox corrente**, con le opzioni
  del runner: exit 1, firma `Read-only file system`, prima di thread.started.
  Nessun indizio osservato di quota, autenticazione o esecuzione del prompt.
- systemctl --user e systemd-run --user: bus negato, Operation not permitted.
  Il figlio sotto systemd non parte. Questa sessione non equivale alla shell host.
- 13 regressioni runner e verifica statica timer passate prima delle modifiche.

Non è dimostrato se ProtectHome/read-only impedisca scritture interne della
CLI sull'host, se intervenga bubblewrap o se vi sia un altro errore.
Non rimuovere ProtectHome, ProtectSystem o NoNewPrivileges alla cieca.
Non cambiare autenticazione, CODEX_HOME, sandbox o privilegi per aggirare il blocco.

## Soluzione preparata e prossimo passo

`diagnose-timer.py` ripete lo stesso prompt innocuo prima direttamente, poi in
un servizio transitorio con le restrizioni dichiarate dall'unità del repository.
Non installa unità, non abilita il runner e non esegue CODEX-TASK.md.
Restituisce solo codici e firme predefinite: nessun transcript, token o percorso
privato. La CLI può effettuare le proprie normali scritture di stato sull'host.
Il servizio transitorio serve per il confronto delle restrizioni: non prova
ancora l'ambiente effettivo dell'unità installata né l'end-to-end del timer.

Unico comando richiesto nella shell host, come utente utente, dalla directory
/opt/ibs-recoverywin-1.0 dopo la chiusura della sessione Codex:

```sh
python3 automation/diagnose-timer.py
```

Se solo il servizio fallisce, il confronto individua il confine systemd da
approfondire prima di una modifica minima e mirata. Se falliscono entrambi,
la causa non è esclusiva del servizio. Se il bus è negato, il confronto non
è stato eseguito. Non ritentare automaticamente gli hash falliti.

Riparazione della causa host e collaudo running → success restano pendenti:
non dichiarare il timer operativo. Nessuna attivazione o modifica dei limiti
systemd è stata effettuata.

Riferimento consultato: [OpenAI, modalità non interattiva](https://learn.chatgpt.com/docs/non-interactive-mode).
