# Verifiche della build 2.0 — 27 ottobre 2026

- Test remoti: 8 test superati; comandi simulati, nessuna connessione TeamViewer reale.
- Test runtime: 8 test superati; inventario in lettura, esclusioni dischi, argomenti QEMU e protocollo.
- Appunti X11: prova reale su display virtuale superata per Unicode, multilinea e testo vuoto.
- WIM WinRE integrata: verifica integrità e dati con wimverify superata.
- ISO WinRE: immagini BIOS e UEFI estratte dal sorgente e inserite come file espliciti; catalogo El Torito verificato e contenuto binario di entrambe confrontato con cmp, identico al sorgente.
- Build live Debian completata con successo: IBS-RecoveryWin-2.0-amd64.hybrid.iso, circa 2,3 GB. Catalogo BIOS/UEFI, MBR ibrido e GPT verificati con xorriso. Kernel, initrd e filesystem SquashFS presenti. WinRE integrata, TeamViewer e launcher WinRE presenti nel filesystem compresso. SHA256 disponibile accanto alla ISO. La presenza delle voci di avvio non dimostra il funzionamento del guest.
- Collaudo della ISO finale e connessione TeamViewer reale ancora da eseguire. Nessuna prova su dischi fisici.

## Correzione TeamViewer dopo collaudo utente

La ISO iniziale è stata avviata realmente in QEMU, con rete NAT e senza dischi fisici. Login SSH admin/admin e desktop XFCE verificati. Riprodotto l’errore grafico «il daemon non è in funzione»: l’autostart apriva la GUI durante i riavvii del servizio necessari per impostare la password.

Correzioni: scrivere EulaAccepted con daemon fermo; richiedere la risposta esatta `ok` dal comando passwd (il wrapper del produttore restituisce zero anche su rifiuto); aprire la GUI solo dopo il completamento di ibs-remote e con teamviewerd attivo.

Applicato il servizio corretto alla VM della live: ibs-remote e teamviewerd attivi, EulaAccepted persistente, ID uguale nel file e nella GUI. La GUI riaperta mostra «Ready to connect (secure connection)», senza procedura di assegnazione account. Questo non prova una connessione remota autenticata: la password deve essere verificata da un secondo client.

11 test remoti superati, compresi rifiuto password con codice zero, configurazione licenza prima dell’avvio e attesa della GUI. ISO corretta in ricostruzione dal chroot originale con i tre file aggiornati; originale preservata.
