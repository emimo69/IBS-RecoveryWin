# R7 — avvio reale firmware OVMF, senza WinRE, solo fixture virtuali

Leggi AGENTS.md, R5-WINRE-TEST-PLAN.md e docs/R6-PREFLIGHT.md. Utente ha autorizzato a procedere al collaudo R7 del firmware UEFI; non ha fornito una ISO WinRE. L'incarico e INTERATTIVO, timer disabilitato. R6 commit aa97dd4 gia pubblicato: non ripeterlo.

Obiettivo concreto: osservare un vero avvio UEFI OVMF con QEMU TCG, isolato, limitato a massimo 10 minuti, senza ISO, disco reale, NAS o USB. Distinguere correttamente successo boot firmware da successo WinRE (quest'ultimo NON testato).

1. Verifica ramo/checkout pulita, versione QEMU e file host reali OVMF_CODE_4M.fd, OVMF_VARS_4M.fd. Per questa sola prova e autorizzato leggere CODE/VARS originali del pacchetto Debian in /usr/share/OVMF e copiare VARS in una directory privata sotto .build, NON modificare gli originali. Controlla percorsi e sha256 prima/dopo; nessun altro progetto o immagine.
2. Crea una base QCOW2 nuova vuota e un overlay SOLO nella directory privata sotto .build, oppure usa solo firmware se un disco virtuale creerebbe un rischio; nessun backing esterno, nessun path /dev nei backend e nessun passthrough. Se crea la base, collega solo overlay alla VM; base immutata. Non usare ISO IBS R2/R3 come CDROM, niente WinRE, niente Acronis.
3. Avvia qemu-system-x86_64 con -machine q35, -accel tcg, -no-user-config -nodefaults, -nic none, pflash CODE readonly, copia VARS rw, SOLO overlay QCOW2 in guest se presente. QMP su socket privato, seriale/log locali, nessun listener TCP/VNC pubblico. Se TCG estremamente lento, interrompi al timeout senza allungarlo. Timer massimo totale 10 minuti, cleanup SIGTERM/SIGKILL e wait/reap obbligatori; no processi QEMU residui.
4. Verifica QMP query-status, query-block e contenuto dell'output firmware/UEFI ove osservabile. Se il boot firmware non e osservabile, descrivi 'non verificato' senza inventare risultato positivo. Conferma backend previsti, numero dischi, rete disabilitata. Il test runtime parser precedente non sostituisce questo boot.
5. Scrivi script di collaudo ripetibile e prudente scripts/test-r7-ovmf-boot.py, con validazioni safety e timeout, non utilizzabile con input dischi fisici. Esegui una sola prova runtime e test rapidi pertinenti. Non compilare ISO o installare pacchetti.
6. Produci docs/R7-OVMF-BOOT.md: comandi, versione e hash firmware, modello virtuale, osservazione effettiva, durata, QMP, prove di hash originali/base invariati, processo chiuso, limiti. Specifica esplicitamente che non hai provato WinRE, TeamViewer, boot Windows o dischi fisici.
7. Se il sistema impedisce l'avvio QEMU o la scrittura, stop non distruttivo con diagnosi concreta. NON disabilitare sandbox, non escalare a root, non creare patch ripetitive. Se git e sola lettura in sandbox, conserva i file e consegna UN comando Git host per add/commit/rebase/push.
8. Non modificare runner/timer, ISO R2/R3, server, rete, TeamViewer, SSH, credenziali, codice non pertinente. Niente WinRE senza ISO autorizzata e richiesta separata.

Consegna: prova OVMF reale circoscritta e rapporto onesto. Al termine arresta la VM, lascia la R3 intatta.
