# IBS-RecoveryWin 2.0 — specifiche concordate (27-10-2026)

## Stato
Nuovo ramo di lavoro, separato da `ibs-recoverywin-1.0`. NON indica una ISO pronta.
Base **richiesta**: IBS-Rescue-PXE 0.6.6 *effettiva* presente sul Debian di build; prima di modificare/buildare confrontare la directory locale, identificare la versione e preservarla integralmente. Non sostituire con IBS-NETBOOT o RecoveryWin 1.0 senza consenso.

## Funzioni richieste
- Live Debian; utente `admin`, password `admin`, login automatico, sudo senza password; SSH avviato al boot con accesso password.
- Disabilitare lock screen, richiesta password dopo inattività e sospensione automatica.
- IP in alto a destra sempre visibile.
- TeamViewer Host: avvio automatico **daemon e GUI**, indipendente dal terminale. Salvare in `/mnt/teamviewer.txt` ID e password **effettivamente valide**. Non inventare password. Se non sono disponibili, riportare chiaramente l'errore e non attestare un successo. Non salvare credenziali nel repository.
- Firefox ESR, Mousepad editor TXT, Thunar.
- QNAP `//192.168.20.123/Public` in `/mnt/nas`, guest, automount/reconnect, senza bloccare il boot quando indisponibile. Icona desktop NAS.
- Integrare la ISO esistente `//192.168.20.123/Public/ISO/IBS-WinRE.iso`, preparata da Windows 11 26H2; verificare esistenza/dimensione/hash locale prima di build; non registrare la ISO binaria su GitHub.
- Pulsante desktop `Avvia Windows RE`: QEMU/KVM con UEFI OVMF e Legacy, esposizione dei dischi fisici rilevanti a WinRE in modalità **lettura/scrittura diretta**, senza overlay QCOW2, snapshot, conferme tramite frasi o password QEMU; non presentare modalità protetta. Escludere il supporto Live/Ventoy per evitare autodistruzione della sessione; non montare contemporaneamente lato host i filesystem guest in scrittura. Configurazione da basare sui test fisici in cui DiskPart vedeva i dischi.
- Pulsante `Incolla in WinRE`: trasferimento di testo dagli appunti Debian a input QEMU anche senza guest agent nel WinRE. Verificare i caratteri critici per comandi Windows: `\\`, `:`, `/`, `"`, `|`, `&`, `>`, `<`, lettere italiane, tasti Invio/Backspace. Non dichiarare implementato senza prova reale.
- Avvio e uscita QEMU affidabili senza finestra congelata, input bloccato o esaurimento della memoria temporanea.

## Vincoli di sviluppo
- Niente cambiamenti alla 0.6.6 stabile o alla vecchia ISO R3.
- Non introdurre restrizioni, credenziali alternative, conferme aggiuntive, overlay o snapshot per scelta autonoma del programmatore.
- Prima identificare i file **locali** della 0.6.6 e la reale ISO QNAP. Se non accessibili da GitHub, fermare integrazione e chiedere il minimo output diagnostico.
- Test statici/unitari mirati e test QEMU isolato prima dell'unica build di collaudo; funzionalità TeamViewer/password e clipboard devono essere validate in test fisico.
- Non alterare partizioni di un cliente nei test: usare disco sacrificabile identificato.
- Tenere distinti: specifiche, codice implementato, ISO compilata e risultati fisici confermati.

## Riferimenti test precedenti
- ISO R3: TeamViewer daemon non partiva, GUI dipendeva dal terminale e password in file non corrispondeva; QEMU spazio /run esaurito, qemu-img fallito, blocchi GTK/input; evitare riuso inconsapevole.
- La stringa esatta `-drive file=/dev/sda,format=raw,if=ide,snapshot=on` era una configurazione **di test protetta**, non è quella definitiva richiesta (scrittura diretta); per la nuova versione rimuovere snapshot esplicitamente.
