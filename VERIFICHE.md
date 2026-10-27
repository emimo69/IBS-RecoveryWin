# Stato dei collaudi — IBS-RecoveryWin 2.0

Aggiornato il 27 ottobre 2026. Le verifiche sulla live 2.0 candidata sono ancora da fare; questa pagina distingue i test completati da quelli pendenti.

## Superato

- `python3 scripts/test-remote.py`: 12 test superati. Verifica parsing ID, attesa ID ritardato, risposta `ok` alla password, rifiuti con codice d’uscita zero, ordine licenza/daemon/GUI e assenza di credenziali obsolete. Sono test con comandi simulati, non una connessione TeamViewer reale.
- `python3 scripts/test-runtime.py`: 8 test superati. Include protocollo appunti, filtri dei dischi, gestione delle race e argomenti QEMU.
- `python3 scripts/test-qemu-block.py`: superati test QEMU come utente `admin` su file e loop basati su file, con settori logici 512 e 4096. Apertura RW via fdset e scrittura verificata nel backing file. Nessun disco fisico usato.
- ISO WinRE integrata generata da `scripts/prepare-winre.py --build-iso`: SHA256 `aa423f0c8a0c71f6627e7cb5ba21b9ac000bec0404c0c3c1e1bcd341b6b34271`. UDF contiene `EFI/Microsoft/Boot/BCD` completo; WIM verificata con `wimverify`.
- Collaudo end-to-end QEMU della ISO WinRE integrata, con QEMU non privilegiato e un solo disco virtuale loop basato su file: avvio UEFI; appunti Unicode bidirezionali con il componente integrato; incolla di testo LF multilinea nel prompt; DiskPart ha scritto GPT con EFI FAT32, MSR e NTFS; uno script incollato ha scritto file sulle partizioni EFI e NTFS; Ctrl+A/Ctrl+C ha riportato la console agli appunti X11. Risultato in `.build/winre-workflow/result.json`. Nessun disco fisico usato.

## In attesa del collaudo della candidata live

- Firefox ESR e il pacchetto di lingua italiana sono stati aggiunti alla lista della prossima build. Da verificare il lancio grafico e la navigazione reale.
- Sul candidato attuale, il primo tentativo SSH è stato fatto mentre `live-config.service` risultava ancora in avvio e la connessione è stata resettata. La password `admin/admin` era stata verificata sulla ISO precedente; ripetere il login sulla candidata quando il bootstrap è finito.
- TeamViewer Host è fissato alla versione 15.82.6 usata dalla Rescue funzionante. Il servizio segue l’ordine Rescue e pubblica ID, password e IP in `/mnt/teamviewer.txt`; deve ancora essere verificato all’avvio della candidata live. Non è stato provato un accesso remoto autenticato da un secondo client.
- L’overlay Conky dell’IP è configurato in alto a destra sotto le icone di servizio; verificarne posizione e aggiornamento nella candidata live.
- Public è configurata come icona sul desktop e mount SMB3 su richiesta. Il montaggio reale e l’icona erano stati verificati in una live precedente; ripetere nella candidata.
- Avviare la ISO live candidata in QEMU e verificare login, WinRE incorporata, TeamViewer, overlay IP e Public. Solo dopo valutare la copia finale sul NAS.

## Limiti

- Nessun disco fisico è stato usato nei test di sviluppo. La prova autorizzata su un dispositivo fisico selezionato va eseguita dall’utente nel proprio ambiente.
- Il test QEMU del backend 4Kn scrive sul loop, ma il riconoscimento del disco 4Kn dentro WinRE non è stato verificato.
- La prova WinRE ha collaudato partizionamento e scritture su EFI/NTFS, non la riparazione dell’avvio di una specifica installazione Windows.
