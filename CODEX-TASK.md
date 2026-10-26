# IBS-RecoveryWin R4D — test parser QEMU OVMF con fixture

Leggi AGENTS.md. R4B e R4C pubblicate: R4C commit 6f8e4c3, 9 test VM, 7 media e 3 di percorsi passati. NON ripetere R4C né riapplicare la patch R4C-review.patch. Conserva R2/R3.

1. Verifica che il repository sia pulito; se trovi file modificati o non tracciati, NON cancellare né sovrascrivere nulla e segnala il blocco.
2. Verifica sintassi reale QEMU per opzioni -drive OVMF, soprattutto virgole duplicate e nomi con spazi. Usa soltanto fixture temporanee, niente NAS, USB, dischi fisici, WinRE/Windows o build ISO. Se puoi testare il parser con QEMU in sicurezza, usa timeout e cleanup garantito. Se non puoi, documenta il limite senza simulare un test reale.
3. Aggiungi test ripetibile non distruttivo; preserva protezione dischi, launcher, SSH, TeamViewer, IP. Esegui test preesistenti.
4. Pubblica docs/R4D-QEMU-VALIDATION.md con comandi/prove reali, limiti e piano per futuro test WinRE con SOLO disco virtuale previa autorizzazione.
5. Commit/push delle sole modifiche validate quando i permessi lo consentono; se sandbox read-only blocca scrittura o git, conserva patch e rapporto locale e dichiara PENDING senza aggirare sandbox.
6. NON modificare timer, servizi, CODEX-TASK.md, ISO R2/R3, cache, altri rami; niente build.

Il task è completato soltanto con test e rapporto pubblicati su GitHub; altrimenti segnala con precisione il blocco.
