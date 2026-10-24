# IBS-RecoveryWin 0.2 — istruzioni per Codex

Questa cartella contiene i sorgenti Debian live-build per IBS-RecoveryWin. Lavorare soltanto su questo repository e sul ramo `fix/ibs-recoverywin-0.2`. Il riferimento dei requisiti è l'issue #1 (`https://github.com/emimo69/IBS-RecoveryWin/issues/1`).

## Regole inderogabili
- Non modificare i progetti esterni `/opt/ibs-recoverywin` (ISO 0.1 stabile), `/opt/ibs-rescue`, `/opt/ibs-rescue-iventoy` o il NAS.
- Non avviare una build ISO prima che tutte le correzioni siano integrate e revisionate. Non committare binari, immagini ISO, cache, chroot, informazioni riservate o credenziali.
- Non fare prove distruttive su dischi reali; tutta la diagnostica e i test automatizzati devono usare dispositivi simulati/file o analisi statica.
- In modalità diretta la VM può scrivere sul disco fisico: identificare e rivalidare il device, avvisare e richiedere conferma esplicita; la modalità protetta deve essere realmente non distruttiva.
- Non rimuovere né smontare `/dev/mapper/ventoy` o `/run/live/medium`: sono usati per l'avvio della Live. Il NAS deve essere opzionale.
- Mai abilitare root SSH senza autenticazione o con password incorporata; progettare un accesso remoto pratico ma sicuro per uso fuori sede.
- Non supporre che l'ISO WinRE sia difettosa: si avvia direttamente, ma va in ciclo di reboot sotto QEMU.

## Priorità di implementazione
1. Diagnosi e riparazione dei percorsi `pkexec`/sessione grafica QEMU protetta e diretta, preservazione corretta di DISPLAY/XAUTHORITY e messaggi errori chiari; controlli di sicurezza sul device.
2. ISO USB Ventoy: gestire correttamente partizione bloccata dal Device Mapper e fallback senza NAS, senza interferire con il boot Live.
3. `it_IT.UTF-8`, tastiera italiana, fuso `Europe/Rome`, XFCE/Zenity in italiano, launcher XFCE attendibili.
4. SSH PuTTY praticabile con credenziali non hardcoded; escludere qualunque accesso indiscriminato di rete.
5. Selettore dischi: escludere NBD, zero byte e device non idonei; ri-verificare il disco lato root prima del lancio.
6. Investigare boot dell'ISO WinRE in QEMU con OVMF e percorsi ISO, conservando le immagini originali.
7. Vera procedura guidata Windows UEFI/BCD: prima analisi sola lettura, poi backup EFI e modifica solo con scelta disco/Windows e conferma esplicita.

## Verifiche richieste
- Individuare tutti gli script coinvolti e spiegare cause effettive prima di intervenire.
- `bash -n` per tutti gli script bash modificati; controlli non distruttivi dei filtri disco e dei percorsi di errore.
- Documentare modifiche, limiti e test in PR. Non dichiarare funzionante una procedura che non è stata verificata su macchina fisica.
- Terminare con PR verso `main`, non unire senza revisione.
