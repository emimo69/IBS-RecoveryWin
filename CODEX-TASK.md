# R5 — Chiusura verifica OVMF e preparazione collaudo WinRE su QCOW2

Leggi AGENTS.md e R4D-PENDING.md. Codex e avviato INTERATTIVAMENTE, non tramite timer. R4B/R4C sono gia completate; R4D-PENDING.md documenta un test reale del parser QEMU con firmware sintetico, non un avvio OVMF. I permessi Linux di docs sono stati corretti. Ultimo push utente ha sincronizzato il ramo ibs-recoverywin-1.0.

OBIETTIVO: riprendere il lavoro utile senza ricominciare test inutili; finalizzare il rapporto R4D e preparare il prossimo collaudo WinRE.

1. Controlla ramo, git status e presenza del test scripts/test-qemu-ovmf-parser.py. NON ripetere la patch R4D-PENDING.patch (gia salvata a riferimento). Non eliminare file di altri task. Se esistono nuove modifiche non tue, fermati e chiedi istruzioni.
2. Esegui il test reale parser QEMU gia implementato in scripts/test-qemu-ovmf-parser.py, 9 test VM, 7 test media, 3 test percorsi, verify-config.sh; se test gia coperti e identici non inventare nuovi collaudi. Nessun boot WinRE/Windows, nessun accesso dischi fisici, NAS o Ventoy. Mantieni ISO R2 e R3 immutate; niente build.
3. Crea docs/R4D-QEMU-VALIDATION.md riportando rigorosamente le prove gia documentate in R4D-PENDING.md, aggiornate ai test realmente rieseguiti. Distingui test parser su fixture da boot OVMF, WinRE, TeamViewer o NAS/USB non verificati.
4. Prepara un piano operativo R5-WINRE-TEST-PLAN.md che preveda OVMF CODE reale read-only, copia temporanea VARS, una ISO WinRE autorizzata read-only e SOLTANTO un disco virtuale QCOW2 con overlay; controlli preliminari e punti di stop, timeout e cleanup, disabilitazione rete VM, nessun passthrough disco. NON avviare ancora WinRE e non utilizzare disco Windows reale.
5. Git: verifica il diff; se git commit/push dalla sandbox viene negato NON creare una catena di patch e NON dichiarare completato. Conserva i file, segnala in modo sintetico all'utente il solo comando necessario nella shell host. Non disabilitare sandbox o richiedere root. Se commit/push consentiti, pubblica e verifica il ramo remoto.
6. Non modificare CODEX-TASK.md, runner/timer, altri progetti, credenziali, token o ISO; nessuna regressione TeamViewer/SSH/IP.

Consegna: rapporto R4D completo e piano sicuro di collaudo WinRE. Lo sviluppo concreto prosegue solo dopo verifica; non consumare tempo sul timer.
