# SMOKE E2E B — collaudo pubblicazione reale e verifica consegna

Leggi AGENTS.md. Questo è un test innocuo del runner, non del progetto Live.

Crea un solo file NUOVO: docs/RUNNER-PUBLISH-SMOKE-B.md
Contenuto esatto:
# Smoke B — pubblicazione automatica
Task: IBS-RecoveryWin runner
Data: 2026-10-26
Codex ha creato questo documento; solo il runner host puo pubblicarlo.

Verifica che il file esista in locale e abbia il contenuto richiesto. Non modificare nessun altro file. Non creare patch o file PENDING. Non eseguire git add, commit, push, pull o fetch: la pubblicazione deve essere fatta dal runner host.

Non eseguire QEMU, ISO, VM, mount, NAS, USB, dischi, servizi, build né interventi di sistema. Non leggere segreti. Non cambiare il timer o altri progetti. Concludi solo dopo avere creato davvero il documento.

Il test e superato soltanto quando docs/RUNNER-PUBLISH-SMOKE-B.md compare come nuovo commit su GitHub, non quando Codex restituisce exit zero.
