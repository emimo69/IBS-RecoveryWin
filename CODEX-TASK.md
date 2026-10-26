# Test E2E runner Git automatico — prova innocua

Leggi AGENTS.md. Questo è SOLO un collaudo end-to-end della nuova pubblicazione Git dal runner host, dopo 13 test offline passati.

1. Crea il file docs/RUNNER-PUBLISH-SMOKE.md con questo contenuto preciso:
# Prova pubblicazione automatica runner
Data: 2026-10-26
Esito del task Codex: file di prova creato per il runner host.
Nessuna ISO, VM, dispositivo fisico o servizio modificato.

2. Non modificare NESSUN altro file. Non creare patch PENDING, rapporti aggiuntivi o backup.
3. Non chiamare git add, git commit, git push o git pull: deve occuparsene il runner host per verificare la nuova funzione.
4. Non avviare ISO, QEMU, servizi, rete, mount, NAS, USB, build o dischi.
5. Termina con esito zero solo dopo aver verificato che il file esista e contenga le quattro righe richieste.

Il runner host deve rilevare il solo file docs/RUNNER-PUBLISH-SMOKE.md, eseguire i test e pubblicarlo. Non dichiarare pubblicazione Git dal processo Codex.
