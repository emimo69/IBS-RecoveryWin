# CODEX-TASK.md — Incarico attuale: preparare controllo automatico incarichi GitHub

**DA ESEGUIRE** quando l'utente dice «Leggi CODEX-TASK.md». Leggi prima AGENTS.md. Opera esclusivamente in /opt/ibs-recoverywin-1.0, ramo ibs-recoverywin-1.0. Il presente incarico sostituisce quello precedente (già completato). Non modificare altri progetti.

## Obiettivo
Preparare (NON attivare ancora) un servizio systemd per la Debian di sviluppo che controlli il repository GitHub ogni 2 minuti e, quando un nuovo CODEX-TASK.md è stato pubblicato da ChatGPT, possa affidarlo a Codex in esecuzione non interattiva. Così non sarà più necessario digitare ogni incarico in PuTTY.

## Requisiti precisi
1. Scrivi uno script di controllo robusto e un servizio + timer systemd **installabili**, ma non installarli né abilitarli in questa fase. Fornisci script di installazione e disattivazione semplici.
2. Monitora SOLO il file CODEX-TASK.md sul ramo ibs-recoverywin-1.0 nel repository emimo69/IBS-RecoveryWin. Usa git fetch o GitHub CLI autenticata; non sovrascrivere modifiche locali non committate.
3. Rileva nuovi incarichi tramite identificativo stabile del contenuto (blob hash di CODEX-TASK.md); registra in uno stato persistente il task già completato. Non rilanciare a ogni commit di Codex se CODEX-TASK.md resta invariato.
4. Impedisci esecuzioni concorrenti con flock; cattura log separati e risultato/exit code. In caso di errore non entrare in un ciclo continuo: lascia una segnalazione leggibile e richiedi intervento manuale o una politica di retry controllata.
5. Il runner deve eseguire Codex con directory di lavoro limitata al nuovo progetto e istruzioni operative di AGENTS.md; rispetta i permessi richiesti dal programma ed evita di usare opzioni di bypass delle approvazioni o sandbox disabilitata. Se non è fattibile in modo completamente non interattivo senza elevare troppo i permessi, documentalo e predisponi una modalità assistita invece di aggirare le autorizzazioni.
6. Non leggere né pubblicare file di credenziali, chiavi, token o contenuti di /mnt/teamviewer.txt nei log.
7. Non autorizzare automaticamente build, cancellazioni, montaggi/scritture su dischi fisici o modifiche ad altri progetti. Il servizio deve essere **disabilitato di default** fino a nostra verifica.
8. Aggiungi controlli statici per timer, flock, deduplicazione e invocazione Codex; eseguili se possibile senza avviare il timer e senza modificare la macchina.
9. Controlla anche, con analisi statica dei sorgenti già pubblicati, che la futura Live abbia l'utente admin/admin, SSH abilitato e TeamViewer con /mnt/teamviewer.txt; segnala difetti veri senza modificare altre funzioni in questo incarico.
10. Esegui commit e push delle modifiche sul ramo ibs-recoverywin-1.0; verifica la coincidenza dell'hash locale/remoto. Riporta commit, file e limiti reali dei test.

**NON compilare ISO. NON attivare il timer. NON eseguire modifiche a dischi o alle versioni precedenti.**
