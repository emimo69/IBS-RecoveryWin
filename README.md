# IBS-RecoveryWin 2.0

Live Debian Trixie amd64 con XFCE italiano, login automatico e SSH attivo: utente `admin`, password `admin`.
Progetto separato dalla 1.0. I requisiti approvati sono in REQUISITI.md.

TeamViewer **Host** si avvia al boot. Il servizio genera una password per ogni sessione live e salva ID, password e IP in `/mnt/teamviewer.txt` (root:admin, 0640). Il collegamento sul desktop apre il file con Mousepad. Il file risiede nella live e non viene salvato sul NAS. La connessione TeamViewer richiede rete; in caso di errore viene pubblicato lo stato, senza credenziali obsolete.

Mousepad e nano modificano file TXT. Nel terminale XFCE: copia `Ctrl+Maiusc+C`, incolla `Ctrl+Maiusc+V`, oppure menu del tasto destro. Clipman gestisce gli appunti della sessione.

## WinRE e dischi

`Avvia WinRE` apre la selezione dei dischi fisici. Quelli selezionati saranno accessibili **in lettura e scrittura**, premendo Avvia WinRE nella finestra di selezione. L’elenco mostra percorso, capacità, modello e seriale. Nessuna selezione avvia WinRE senza dischi fisici.
Sono esclusi dischi montati, swap, dischi con dipendenze RAID/LVM e supporto della live; non vengono smontati automaticamente. La presa esclusiva del kernel impedisce il montaggio dei dischi assegnati durante la sessione QEMU. Le dimensioni dei settori 512/4096 sono preservate. Massimo cinque dischi: controller SATA emulato per settori logici da 512 byte, NVMe emulato per settori logici da 4096 byte (il controller IDE QEMU rifiuta i dischi 4Kn). Il driver stornvme.sys è presente nella WIM; il riconoscimento nel guest dei dischi 4Kn resta da collaudare. I privilegi root servono soltanto all’apertura controllata dei dischi; QEMU gira come admin.

WinRE parte su richiesta dal desktop, con UEFI, 2 CPU, 2 GB RAM e KVM quando accessibile (TCG altrimenti). La ISO QNAP viene inclusa nella live: non è necessario collegarsi al NAS durante l’uso. Il sorgente NAS è stato copiato e verificato SHA256, senza modificarlo.

Un componente Windows nativo condivide il testo Unicode degli appunti tra Debian e WinRE attraverso il canale privato QEMU; non apre porte sulla rete fisica e non richiede driver SPICE. Non trasferisce file o immagini. L’avvio WinRE integrato inizializza WinPE, attiva il componente, apre il prompt e mantiene l’ambiente grafico di ripristino. Nel prompt Windows si usano Ctrl+C/Ctrl+V con le scorciatoie abilitate; le prove della ISO finale devono confermare anche l’interazione grafica.

## Preparazione e compilazione

Le ISO e i binari generati non sono su GitHub. Sorgente WinRE: `/mnt/ibs-iso/ISO/IBS-WinRE.iso` (SHA256 in assets/WinRE.sha256), da copiare in `config/includes.chroot/opt/ibs/iso/IBS-WinRE.iso`.
Dipendenze di preparazione: live-build, xorriso, wimtools e gcc-mingw-w64-x86-64-win32. I test richiedono QEMU, OVMF, xvfb, xclip e xauth.

`python3 scripts/prepare-winre.py` compila il componente e prepara/verifica solo la WIM, senza produrre ISO. La WIM preparata rimane in `.build`.
**Solo dopo autorizzazione esplicita alla compilazione:** `sudo scripts/build-iso.sh --authorized`. Lo script integra la WIM nella copia locale WinRE preservando l’avvio BIOS/UEFI, quindi esegue live-build. Il hook blocca una build con WinRE non integrata. Le operazioni si eseguono dalla radice della 2.0. Non usare la directory 1.0.

## Verifiche

`python3 scripts/test-remote.py`: parsing ID, errori, assenza di credenziali obsolete e permessi del file con comandi simulati; non prova una connessione TeamViewer reale.
`sudo python3 scripts/test-qemu-block.py`: apre dispositivi loop temporanei basati esclusivamente su file; verifica QEMU come uid 1000, fdset e scrittura reale su file e dispositivi a blocchi 512/4096. Non avvia WinRE e non usa dischi fisici.
`python3 scripts/test-runtime.py`: protocollo appunti, inventario reale in sola lettura, esclusioni dischi, gestione race e argomenti QEMU.
`python3 scripts/test-clipboard-x11.py`: scambio testo reale con gli appunti X11 su display virtuale.
`python3 scripts/test-winre-boot.py start`: avvia la ISO WinRE esistente con soli dischi di test basati su file, senza compilare ISO. Il comando `stop` termina la VM. Comandi `screen`, `key` e `type` consentono di ispezionare il guest (layout italiano).
`python3 scripts/test-clipboard-winre.py`: prova gli appunti Windows/X11 dalla VM già avviata al prompt e con rete WinPE inizializzata.

Stato delle verifiche e limiti: vedere VERIFICHE.md. Nessuna dichiarazione di funzionamento della live completa prima del collaudo della ISO finale.
