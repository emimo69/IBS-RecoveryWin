# R4B — BLOCCATO, non completato e non pubblicato

## Prove PASSATE (con comando)
- `python3 -B scripts/test-vm.py`: 8 test esistenti passati, policy UEFI/Legacy, protezione Live/Ventoy, backing readonly/overlay e fd su fixture.
- `python3 -B scripts/test-media.py`: 7 test esistenti passati, mount Ventoy mock readonly, percorsi con spazi/virgole e configurazione NAS statica.
- `bash scripts/verify-config.sh`: passato, inclusa verifica remota statica e git diff --check. Nessuna build.
- Verifica documentazione QEMU: /usr/share/doc/qemu-system-common/system/invocation.html e https://qemu-project.gitlab.io/qemu/system/invocation.html prescrivono il raddoppio delle virgole in file=.
- Prova non distruttiva con os.open(O_CREAT|O_EXCL): creazione nella root progetto riuscita e rimossa; in .git fallisce con errno 30, Read-only file system. .git/index.lock assente. Processo UID/GID 1000; scripts/test-vm.py UID/GID 65534 e modo 0664. apply_patch sul test fallito. Non sono stati aggirati permessi.

## Limiti non ancora collaudati
Avvio WinRE/Windows reale; NAS/USB reali; connessione remota esterna.
Il difetto file= OVMF è presente; la patch proposta R4B-proposed.patch è salvata ma NON applicata né verificata. Il nuovo test non è stato eseguito. La suite esistente non dimostra che il difetto sia risolto. Selezione ISO NAS/Ventoy completa e parser QEMU reale restano da verificare.
Commit impossibile perché .git è montata in sola lettura; push non tentato. Nessuna pubblicazione GitHub. CODEX-TASK.md invariato.

## Prossimo collaudo necessario
Riprendere in un ambiente autorizzato con file sorgenti e .git scrivibili. Riprodurre il fallimento del nuovo test prima della correzione, applicare e verificare la patch minima a CODE/VARS senza cambiare -blockdev JSON; completare mock selezione ISO NAS/Ventoy e controllo parser QEMU su fixture, rieseguire le verifiche consentite e aggiornare questo rapporto. Quindi commit/push e verifica remota. Nessuna build ISO autorizzata.
