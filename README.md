# IBS-RecoveryWin 1.0

Prima configurazione live-build: Debian Trixie amd64, XFCE in italiano,
tastiera italiana e fuso Europe/Rome. Nessuna ISO compilata.

- Utente live `admin`, password `admin`, gruppo sudo e login automatico LightDM.
- SSH con password, accesso consentito solo ad admin; chiavi host generate al boot.
- NetworkManager e TeamViewer avviati automaticamente.
- Conky mostra sul desktop ID e password TeamViewer, generata a ogni avvio.
  Il file riporta anche gli indirizzi IP locali assegnati. Le credenziali sono in `/mnt/teamviewer.txt`, leggibili solo da root/admin.
  Errori e ID non disponibile sono mostrati esplicitamente; per riprovare:
  `sudo systemctl restart ibs-remote`.
- Nessuna implementazione NAS, creazione USB o QEMU.

## Preparazione senza compilazione

Dalla directory `/opt/ibs-recoverywin-1.0`, eseguire `./auto/config`.
Questo genera soltanto la configurazione di live-build; non esegue build.
La compilazione richiede una successiva autorizzazione esplicita.

Il futuro hook chroot scarica il pacchetto amd64 dal sito ufficiale TeamViewer
tramite HTTPS e installa le dipendenze. Il pacchetto segue la versione corrente:
la build non è riproducibile bit per bit e richiede rete. Il servizio imposta
l'accettazione della licenza TeamViewer per consentire l'avvio automatico.
L'utilizzo resta soggetto alla licenza del produttore.

## Verifiche

Eseguire `./scripts/verify-config.sh` per controllare sintassi e impostazioni.
Queste verifiche non avviano servizi e non modificano dischi fisici.
Prima di dichiarare la live operativa occorrono, dopo autorizzazione alla build,
avvio reale, verifica lingua/login, accesso SSH da un secondo computer,
connessione TeamViewer con le credenziali visualizzate e controllo al riavvio.
Le credenziali admin/admin sono quelle richieste per questa prima fase.

Riferimenti: [Debian Live Manual](https://live-team.pages.debian.net/live-manual/html/live-manual.en.html)
e [TeamViewer CLI](https://www.teamviewer.com/it/global/support/knowledge-base/teamviewer-remote/download-and-installation/linux/install-teamviewer-classic-on-linux-without-graphical-user-interface/).

Il launcher **TeamViewer ID e Password** viene creato nella cartella desktop
localizzata di admin all'accesso XFCE e apre `/mnt/teamviewer.txt` con Mousepad.
Lo script applica modo 0755 e il checksum GVFS `metadata::xfce-exe-checksum`
nella sessione utente, con tentativi per attendere la disponibilità dei metadati.
Il file di assistenza è pubblicato atomicamente con proprietario root:admin e
modo 0640; /mnt resta attraversabile (0755). Password e ID vengono mostrati
solo dopo esito positivo di `teamviewer passwd`, ID numerico e IP disponibile.
Durante preparazione o errore viene mostrato un messaggio senza credenziali.
L'assegnazione dell'ID e l'esito della CLI non provano una connessione remota.

Verifica statica del launcher basata sul [meccanismo di attendibilità XFCE](https://developer.xfce.org/libxfce4util/libxfce4util-GIO-Extensions.html).
La creazione e l'attendibilità nel desktop richiedono ancora collaudo nella live.
