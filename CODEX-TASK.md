# R6 — preflight per collaudo WinRE su QCOW2

Leggi AGENTS.md e R5-WINRE-TEST-PLAN.md. Codex lavora INTERATTIVAMENTE. R5 gia pubblicata: non ripeterla.

Obiettivo: verificare i prerequisiti del futuro boot WinRE reale prima di avviarlo; questo incarico NON autorizza il boot WinRE, la creazione di dischi reali o compilazioni ISO.

1. Verifica branch ibs-recoverywin-1.0, checkout pulita. Non toccare altri progetti, ISO R2/R3 o timer.
2. In sola lettura verifica qemu-system-x86_64, qemu-img, OVMF CODE/VARS reali compatibili, /dev/kvm e spazio disponibile. Cerca possibili ISO WinRE solo nei percorsi locali del progetto e /opt/ibs-recoverywin-test; niente NAS, USB, /dev o media fisici. Documenta disponibilita effettiva, versioni e limiti. Non scegliere altre ISO in sostituzione.
3. Implementa scripts/preflight-r6-winre.py: deve controllare file e percorsi ISO/firmware/QCOW2 passati esplicitamente, rifiutare device, symlink sospetti, /dev, /proc, /sys, NAS e USB, immagini incoerenti e catene QCOW2 inattese. Non lanciare QEMU o scrivere immagini. Errori comprensibili e status nonzero.
4. Implementa scripts/test-r6-preflight.py: test offline con fixture in cartelle temporanee, senza dischi reali e senza privilegi; verifica anche rifiuto dei casi pericolosi.
5. Scrivi docs/R6-PREFLIGHT.md con prove, eventuale mancanza di KVM, ISO WinRE ancora da indicare/autorizzare, piano di lancio isolato OVMF con una sola QCOW2 quando sara autorizzato.
6. Esegui i test nuovi e i controlli statici opportuni senza rifare lunghe procedure gia concluse; git diff --check. Se la sandbox blocca git commit/push, conserva i file e dai un solo comando breve per la shell host. Non modificare runner, servizi, codice TeamViewer/SSH, ISO, credenziali, pacchetti o rete. Nessuna build.
7. Non dichiarare avvenuto boot WinRE o Windows: e solo la fase preparatoria. Stop prima di qualunque operazione su dischi o VM.

Consegna: verifiche preliminari R6 concrete, script preflight e test, documento dei prerequisiti.
