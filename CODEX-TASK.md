# IBS-RecoveryWin R4B — correggere davvero QEMU/OVMF e provare il risultato

Questo task sostituisce R4, il cui runner è terminato con exit_code 0 ma SENZA commit di sviluppo né rapporto R4. Il successo di un processo non prova che il lavoro richiesto sia stato eseguito. Leggi AGENTS.md. Opera SOLO nel ramo ibs-recoverywin-1.0 e nella cartella /opt/ibs-recoverywin-1.0. Conserva ISO R2/R3, SSH/TeamViewer, indicatore IP, launcher, cache e stato timer.

## Prima: definire il difetto e testarlo
- In config/includes.chroot/usr/local/lib/ibs-recovery/vm.py, qemu_args() passa a QEMU le opzioni '-drive' OVMF con 'file=' e percorsi raw che possono contenere virgole (QEMU separa i campi sulle virgole anche senza shell). Riproduci il caso in un test unitario di scripts/test-vm.py con CODE e VARS aventi virgole e spazi. Verifica la sintassi ammessa da QEMU per l'escape delle virgole (normalmente duplicazione delle virgole nel valore dell'opzione). Non cambiare gli argomenti '-blockdev' JSON che gestiscono correttamente tali caratteri.
- Applica la correzione minima a entrambi i percorsi OVMF e supera il nuovo test. Nessuna build ISO in questo task.

## Poi: verifiche non distruttive
- Testa in modo statico/mock la selezione ISO per NAS e Ventoy, il quoting dei nomi con spazi, le opzioni UEFI/Legacy, la protezione del disco Live/Ventoy e il backing readonly/overlay. Usa SOLO fixture: mai NAS, USB o dischi fisici reali.
- Esegui python3 -B scripts/test-vm.py, gli altri test esistenti utili e bash scripts/verify-config.sh; se un test è assente indica l'alternativa usata.
- Crea docs/R4-PROGRESS.md con tre sezioni: prove PASSATE (con comando), limiti non ancora collaudati (avvio WinRE/Windows reale; NAS/USB reali; connessione remota esterna), e prossimo collaudo necessario.
- Commit e push delle sole modifiche testate, non forzare Git. Mantieni CODEX-TASK.md immutato.

## Se non puoi scrivere o fare commit nella sandbox
- Non terminare dicendo 'completato' o 'success' se non ci sono patch e rapporto su GitHub.
- Determina con una prova NON distruttiva se il problema è il filesystem in sola lettura, .git/index.lock, oppure permessi; indica esattamente il limite. Se scrivibile solo la working tree, salva patch e rapporto localmente e NON dichiarare R4 completata. Mai bypass dei permessi o sandbox.
- Se tutti i controlli sono già corretti per altri motivi, documenta con prove verificabili e salva almeno il rapporto su GitHub; niente modifiche artificiali.

## Sicurezza
Niente comandi root, scrittura dischi, reboot host, nuove VM su dischi fisici, ISO build, modifiche alla base stabile o altri progetti. Niente azioni sulla configurazione del timer. Non avviare doppie sessioni Codex.

**Esito richiesto:** per R4B sono necessari patch/test verificati e docs/R4-PROGRESS.md pubblicati. Se mancano, segnala il blocco e fermati.
