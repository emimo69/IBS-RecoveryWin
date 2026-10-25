# Funzioni di recupero R3 e limiti del collaudo

## Desktop e origini ISO

Conky rimane nell'angolo alto destro e conserva l'assistenza TeamViewer.
Il nuovo indicatore interroga `ip -j address` ogni due secondi: ethernet/wifi,
indirizzi globali, cambio DHCP, IPv6 se manca IPv4 e messaggio senza IP.
Non legge /mnt/teamviewer.txt: la funzione TeamViewer preesistente è separata.

L'icona **Monta ISO** sceglie UEFI OVMF o Legacy e poi l'origine:
NAS QNAP Public/ISO con SMB3 guest, oppure partizione dati USB Ventoy.
Il NAS è montato ro/nosuid/nodev/noexec, senza password o file credenziali,
con prefixpath=ISO. L'ambiente del mount non eredita credenziali SMB.
Il server QNAP deve consentire realmente l'accesso guest e la rete deve essere
raggiungibile: questo non è stato provato montando il NAS sul server di sviluppo.

Ventoy è riconosciuta da label Ventoy o da partizione dati 1 sullo stesso
supporto USB di VTOYEFI (anche se rinominata). La EFI non viene selezionata.
I mountpoint sono letti come array JSON, senza concatenare sequenze letterali
backslash-n. Se i dati sono già montati, si crea una vista bind separata in
sola lettura, senza rimontare l'originale; viste già aperte sono riutilizzate
solo se device e ro corrispondono. Nuovi mount sono ro, con uid/gid di admin e umask 022 per poter leggere
i file anche se l’helper ha umask privata; NTFS usa norecover.
Supportati exFAT, FAT e NTFS; altri filesystem non vengono montati alla cieca.
Nessuna formattazione, riparazione o scrittura USB è implementata dal selettore.

Zenity fornisce avanzamento, errori e selettore *.iso/*.ISO/*.Iso. I percorsi
con spazi e virgole passano come argomenti separati o JSON, senza shell.
I file ISO risolti devono restare nella sorgente selezionata sotto /run/ibs-media.
L'helper privilegiato rifiuta il server: richiede root, boot=live e
hostname=ibs-recoverywin. Il desktop admin usa sudo già previsto dalla base.

## ISO e OS da disco sono distinti

**Monta ISO** avvia soltanto la ISO selezionata come CD-ROM read-only.
**Avvia sistema operativo da disco** seleziona un disco intero, senza ISO.
Entrambe le modalità propongono UEFI (OVMF CODE read-only e VARS nuova di
sessione) o Legacy. QEMU gira come admin, non come root. Non è stato copiato
o modificato firmware del server. Un OS UEFI può richiedere la selezione
manuale di EFI/Microsoft/Boot/bootmgfw.efi nel nuovo firmware virtuale.

WinRE e modalità OS richiedono KVM realmente esposto nella Live (API 12),
CPU host. Un host esterno con KVM non implica KVM nel guest: in una Live
virtuale serve anche configurazione nested corretta. Senza KVM WinRE/OS sono
rifiutati con messaggio chiaro; altre ISO possono usare TCG soltanto dopo
conferma. Nessuna compatibilità Acronis/WinRE/altra ISO è dichiarata da questi
sorgenti. Una VM da 2 GiB richiede almeno 2,5 GiB disponibili nella Live.

## Protezione dischi

Selezione da inventario fresco lsblk, disco intero, identità hash con numero
major:minor, dimensione e seriale; revalidazione prima e dopo apertura.
Ventoy/VTOYEFI, dischi montati (incluso supporto Live), swap e volumi attivi
RAID/LVM/crypt/holders sono esclusi. Se il mount di origine Live non è
identificabile, ad esempio toram/supporto rimosso, l'avvio OS è rifiutato.

La modalità predefinita è **protetta**: dispositivo aperto O_RDONLY e O_EXCL,
fd passato tramite fdset QEMU, nodi file/base esplicitamente read-only e un
QCOW2 di sessione separato con backing configurato nel grafo QEMU. Non si
usa -snapshot su una base aperta in scrittura. O_EXCL aggiunge la verifica
kernel di dispositivo occupato; le scritture restano nell'overlay in RAM.
Overlay e VARS rimangono nella sessione /run/ibs-media/vms fino al riavvio:
non c'è commit automatico delle modifiche al disco.

La scrittura diretta è un'opzione distinta, disattivata per default: avviso
esplicito e frase SCRIVI + dispositivo + parte del token, poi nuova validazione
e apertura esclusiva O_RDWR. Non è stata mai eseguita durante questo incarico.
Le protezioni sui dispositivi reali richiedono ancora collaudo su hardware o
su dischi virtuali fittizi esposti come block device in una Live con KVM.

## Test disponibili

- `python3 scripts/test-desktop-ip.py`: ethernet/wifi, cambio indirizzo,
  nessun IP, IPv6, esclusione loopback/down.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/test-media.py`: Ventoy rinominata,
  già montata, device cambiato, mount bind ro, percorsi con spazi/virgole/Unicode.
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/test-vm.py`: policy dischi,
  UEFI/Legacy, KVM/TCG, grafi, fd read-only reale su file fittizio e conferme.
- `python3 scripts/test-qcow2-fixture.py`: crea soli file QCOW2 da 64 MiB
  in .build, legge il backing, scrive l'overlay con qemu-io, verifica pattern
  diversi, hash base invariato e qemu-img check. Non avvia VM o Windows.
- Test R2 `test-remote.py`, `test-launcher.py`, verify-config e preflight:
  conservano verifica SSH/config, TeamViewer, launcher e TXT.

I test mock non equivalgono a prova NAS, Ventoy reale, OVMF/WinRE, Acronis o
Windows. Per WinRE e OS serve un host con KVM, KVM esposto nella Live e un
**disco virtuale di prova contenente un OS**, senza dischi fisici. Non usare
il QCOW2 Windows 64 GB esistente in altri progetti per il test R3.

Il test finale R3 avvia esclusivamente la Live senza dischi, in TCG sul server,
con timeout e spegnimento; controlla SSH/servizi R2, IP e launcher/metadata,
senza leggere credenziali e senza montare NAS/USB reali o avviare QEMU annidato.
Risultati effettivi e SHA256 sono in [TEST-1.0-R3-RESULTS.md](TEST-1.0-R3-RESULTS.md).

Riferimenti: [QEMU fdset/read-only/backing](https://www.qemu.org/docs/master/system/invocation.html),
[lsblk JSON](https://manpages.debian.org/trixie/util-linux/lsblk.8.en.html),
[mount.cifs guest](https://manpages.debian.org/trixie/cifs-utils/mount.cifs.8.en.html),
[open O_EXCL su block device](https://manpages.debian.org/trixie/manpages-dev/open.2.en.html).
