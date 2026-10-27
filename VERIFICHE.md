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

11 test remoti superati, compresi rifiuto password con codice zero, configurazione licenza prima dell’avvio e attesa della GUI. ISO corretta generata dal chroot originale con i tre file aggiornati: IBS-RecoveryWin-2.0-fix-teamviewer-amd64.hybrid.iso. I tre file sono stati riletti dal filesystem SquashFS e confrontati byte per byte con i sorgenti. Catalogo BIOS/UEFI verificato. Originale preservata; la prova grafica riguarda la live originale con servizio aggiornato, non un nuovo avvio completo della ISO corretta.

## Correzione dischi QEMU

Errore segnalato dall’utente: il driver `file` richiedeva un file regolare per `/dev/fdset/1`. Ora il backend è scelto con fstat: `host_device` per descrittori a blocchi, `file` per i file di test. Non cambia l’apertura esclusiva e non vengono riaperti percorsi di dischi dopo il calo dei privilegi.

Test QEMU reale eseguito come uid 1000 con fdset: lettura/scrittura e verifica di 4096 byte nel file sottostante superate su file regolare, loop con settori 512 e loop con settori 4096. Tutti i loop sono stati creati appositamente da file temporanei e rimossi a fine test; nessun disco fisico usato.

Il test ha rilevato anche che IDE QEMU rifiuta settori logici 4096. Questi usano ora NVMe emulato; stornvme.sys è presente nella WIM. Il test prova l’apertura e la scrittura dal backend QEMU, non il riconoscimento 4Kn in WinRE né la selezione grafica nella live. La ISO con entrambe le correzioni è stata generata: IBS-RecoveryWin-2.0-fix-teamviewer-winre-amd64.hybrid.iso (circa 2,3 GB). vm.py, ibs-remote, ibs-teamviewer-ui e il file autostart sono stati riletti dal filesystem SquashFS e confrontati byte per byte con i sorgenti. Catalogo BIOS/UEFI verificato. Non è ancora stato eseguito un nuovo avvio completo di questa ISO.

## Appunti WinRE dopo la segnalazione

Nella VM WinRE di test già avviata, test-clipboard-winre.py ha verificato lo scambio reale Unicode e multilinea fra CF_UNICODETEXT Windows e X11 in entrambe le direzioni. Successivamente test-clipboard-winre-gui.py ha impostato un comando negli appunti Linux, incollato con Ctrl+V nel prompt WinRE ed eseguito Invio: risultato del comando osservato nello screenshot. Ctrl+A/Ctrl+C ha copiato il contenuto della console verso X11, dove il marcatore è stato rilevato insieme al prompt Windows.

Il componente Windows è stato avviato dal disco ausiliario della VM di test, non dal desktop di una nuova sessione della ISO finale. Il test non prova l’avvio automatico integrato nella ISO finale. Nessun disco fisico usato.

## Public sul desktop

Confermato accesso SMB ospite con smbclient e montaggio reale SMB3 in sola lettura su directory temporanea del progetto; smontato dopo verifica. Configurate unità mnt-Public.mount e mnt-Public.automount, validate con systemd-analyze verify. Collegamento Desktop/Public verso /mnt/Public. Installato cifs-utils nel chroot e aggiunto alla lista pacchetti; abilitato automount. Nessuna credenziale NAS incorporata. La presenza e il funzionamento di Public nella nuova live restano da verificare dopo la compilazione.

## Confronto con IBS Rescue e prova della live con Public

Consultato su richiesta dell’utente IBS-NETBOOT, commit 4ead382, script ibs-rescue/usb/config/includes.chroot/usr/local/sbin/ibs-teamviewer-auto e variante PXE. La Rescue chiude la GUI prematura e la riaggancia alla sessione XFCE; controlla esplicitamente la risposta ok alla password.

La prima ISO con Public è stata avviata integralmente in QEMU: admin/admin, credenziali e licenza presenti, automount Public abilitato. L’elenco della directory ha attivato un montaggio CIFS reale di //192.168.20.123/Public su /mnt/Public, e il collegamento è visibile sul desktop. La schermata ha però rivelato una GUI TeamViewer prematura attivata tramite D-Bus.

Ripreso dalla Rescue il riaggancio della GUI: il launcher della 2.0, dopo il servizio pronto, chiude soltanto il processo TeamViewer del proprio utente e lo riapre con l’ambiente della sessione XFCE. La correzione applicata alla live ha eliminato l’errore: schermata Ready to connect e ID uguale al TXT. Non è stata provata una connessione remota autenticata. La ISO viene ricostruita con questo launcher aggiornato.
