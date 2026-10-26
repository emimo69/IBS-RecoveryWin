# Smoke C — prova end-to-end con runner aggiornato

Leggi AGENTS.md. Questo incarico testa solo la consegna automatica di un file testuale. Non usare git add, commit, push, pull, fetch; li esegue il runner host.

Crea ESATTAMENTE un file nuovo: docs/RUNNER-PUBLISH-SMOKE-C.md

Contenuto richiesto:
# IBS RecoveryWin — smoke C
Data: 2026-10-26
Obiettivo: verificare consegna e pubblicazione automatica dal runner.
Nessun disco, ISO, servizio o macchina virtuale modificati.

Verifica con controllo locale che esista, sia un file ordinario e abbia esattamente queste quattro righe. Non toccare altri file; non creare rapporti, backup o patch aggiuntive. Non modificare CODEX-TASK.md.

Non accedere a credenziali, dispositivi fisici, NAS, USB, VM o servizi. Nessuna build. Non eseguire QEMU. Non disabilitare sandbox o permessi. Se il file non può essere creato, termina segnalando fallimento.

L'esito atteso è un commit GitHub nuovo contenente docs/RUNNER-PUBLISH-SMOKE-C.md. Un exit zero senza file non costituisce successo.
