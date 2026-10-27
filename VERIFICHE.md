# Stato dei collaudi — IBS-RecoveryWin 2.0

Aggiornato il 27 ottobre 2026 dopo il collaudo della live candidata.

## Superato

- `python3 scripts/test-remote.py`: 12 test superati. Verifica parsing ID, attesa ID ritardato, risposta `ok` alla password, rifiuti con codice d’uscita zero, ordine licenza/daemon/GUI e assenza di credenziali obsolete. Sono test con comandi simulati, non una connessione TeamViewer reale.
- `python3 scripts/test-runtime.py`: 8 test superati. Include protocollo appunti, filtri dei dischi, gestione delle race e argomenti QEMU.
- `python3 scripts/test-qemu-block.py`: superati test QEMU come utente `admin` su file e loop basati su file, con settori logici 512 e 4096. Apertura RW via fdset e scrittura verificata nel backing file. Nessun disco fisico usato.
- ISO WinRE integrata generata da `scripts/prepare-winre.py --build-iso`: SHA256 `aa423f0c8a0c71f6627e7cb5ba21b9ac000bec0404c0c3c1e1bcd341b6b34271`. UDF contiene `EFI/Microsoft/Boot/BCD` completo; WIM verificata con `wimverify`.
- Collaudo end-to-end QEMU della ISO WinRE integrata, con QEMU non privilegiato e un solo disco virtuale loop basato su file: avvio UEFI; appunti Unicode bidirezionali con il componente integrato; incolla di testo LF multilinea nel prompt; DiskPart ha scritto GPT con EFI FAT32, MSR e NTFS; uno script incollato ha scritto file sulle partizioni EFI e NTFS; Ctrl+A/Ctrl+C ha riportato la console agli appunti X11. Risultato in `.build/winre-workflow/result.json`. Nessun disco fisico usato.

## Collaudo della candidata live

- Avvio UEFI in QEMU con la ISO candidata, rete NAT e solo unità CD-ROM. Nessun disco fisico collegato.
- SSH con `admin/admin` riuscito; il servizio `ibs-remote` termina con successo e `teamviewerd` resta attivo.
- TeamViewer Host 15.82.6 ha prodotto ID e password personali. L’ID nel file corrisponde all’ID riportato da `teamviewer info`; `/mnt/teamviewer.txt` ha permessi `0640` ed è di proprietà `root:admin`. La GUI/icone TeamViewer si avviano nella sessione XFCE. Non è stata provata una connessione autenticata da un secondo client.
- Conky mostra l’indirizzo IPv4 in alto a destra sotto la barra e le icone dei servizi (posizione osservata in QEMU: x=1016, y=37 nella finestra 1280x800).
- L’icona Public è sul desktop. L’accesso a `/mnt/Public` ha attivato il mount SMB3 reale `//192.168.20.123/Public` e ha elencato contenuti del NAS.
- Firefox ESR è stato avviato nella sessione grafica; la finestra ha caricato `www.debian.org` con titolo “Debian -- The Universal Operating System”. Una richiesta HTTPS a `https://www.debian.org` ha restituito HTTP 200.
- La ISO candidata è stata generata in modalità BIOS/UEFI. SHA256: `3bc8d8b659bddeb984d06208a1829631066ca4f467ecb71904672dc192a5e5ea`.

## Limiti

- Nessun disco fisico è stato usato nei test di sviluppo. La prova autorizzata su un dispositivo fisico selezionato va eseguita dall’utente nel proprio ambiente.
- L’accesso TeamViewer da un client esterno non è stato provato; la verifica live conferma servizio, generazione e pubblicazione locale delle credenziali.
- Il test QEMU del backend 4Kn scrive sul loop, ma il riconoscimento del disco 4Kn dentro WinRE non è stato verificato.
- La prova WinRE ha collaudato partizionamento e scritture su EFI/NTFS, non la riparazione dell’avvio di una specifica installazione Windows.
