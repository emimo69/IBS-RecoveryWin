# Verifiche della build 2.0 — 27 ottobre 2026

- Test remoti: 8 test superati; comandi simulati, nessuna connessione TeamViewer reale.
- Test runtime: 8 test superati; inventario in lettura, esclusioni dischi, argomenti QEMU e protocollo.
- Appunti X11: prova reale su display virtuale superata per Unicode, multilinea e testo vuoto.
- WIM WinRE integrata: verifica integrità e dati con wimverify superata.
- ISO WinRE: immagini BIOS e UEFI estratte dal sorgente e inserite come file espliciti; catalogo El Torito verificato e contenuto binario di entrambe confrontato con cmp, identico al sorgente.
- Build live Debian in corso; la presenza delle voci di avvio non dimostra il funzionamento del guest.
- Collaudo della ISO finale e connessione TeamViewer reale ancora da eseguire. Nessuna prova su dischi fisici.
