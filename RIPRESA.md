# Checkpoint IBS-RecoveryWin 2.0 — 27 ottobre 2026

## Obiettivo e autorizzazioni

Lavorare esclusivamente in /opt/ibs-recoverywin-2.0. Leggere AGENTS.md. Utente autorizza compilazione e salvataggio finale in /mnt/ibs-iso/ISO, MA soltanto dopo collaudo reale WinRE/QEMU: selezione dischi a blocchi RW, DiskPart GPT/EFI/NTFS, incolla script multilinea nel prompt e copia inversa. Test di sviluppo soltanto su dispositivi virtuali basati su file. Vuole TeamViewer funzionante con ID/password/IP in /mnt/teamviewer.txt; IP sempre visibile in alto a destra sotto icone servizi; cartella Public del NAS sul desktop. Ha autorizzato pulizia ISO fallite e duplicati inutili. Non ha chiesto di azzerare i sorgenti: «forse partiamo da zero» era condizionale.

Nessuna ripresa automatica alle 16:59 è stata programmata: mancano strumenti di riattivazione della sessione. Utente è stato avvisato di scrivere «continua» se il limite interrompe il lavoro.

## Punti fermi

- NAS Public: //192.168.20.123/Public, montato host su /mnt/ibs-iso; destinazione ISO /mnt/ibs-iso/ISO. Accesso ospite SMB3 realmente verificato.
- Rescue funzionante richiesta dall'utente: /mnt/ibs-iso/ISO/IBS-Rescue-PXE-0.6.6.iso. Già montata RO: /mnt/ibs-base-066 e /mnt/ibs-root-066 (loop0/loop1). NON alterare/detach questi due loop.
- Rescue include TeamViewer Host 15.82.6. La 2.0 scaricava latest 15.83.3: ora fissato pacchetto .build/teamviewer-host.deb (15.82.6), SHA256 in assets/TeamViewer-15.82.6.sha256. Daemon identico alla Rescue (hash confrontato). Build hook usa config/includes.chroot/tmp/teamviewer-host.deb, verifica SHA/versione e apt-mark hold. build-iso.sh ripristina asset dalla cache se manca. Binari/ISO non su GitHub.
- ibs-remote ora riprende l'ordine della Rescue reale: license accept; riavvio daemon; attesa XFCE; riaggancio GUI con ambiente letto da /proc del processo XFCE; attesa ID; password alfanumerica 8 caratteri maiuscole/minuscole/numeri impostata PER ULTIMA, verifica risposta ok; pubblicazione atomica TXT 0640 root:admin, nessuna copia credenziali sul NAS. Autostart GUI separato rimosso. Unit retry e timeout esteso. 12 test remoti passati dopo porting; verificarli se si modifica ancora.
- Chroot ha già TeamViewer 15.82.6 e conky-std installati. Overlay IP aggiunto in config/includes.chroot/etc/conky/ibs-ip.conf, autostart ibs-local-ip.desktop e script ibs-local-ip (aggiorna IP ogni 5s, top_right gap_y42). Da verificare graficamente.
- Public: mnt-Public.mount + .automount, Desktop/Public -> /mnt/Public, cifs-utils installato. Verificato nella live precedente: montaggio CIFS reale su accesso e icona desktop visibile.
- vm.py: file.driver=host_device per fstat S_ISBLK; file per fixture regolari. fdset mantiene RW esclusivo e probe RO. Test QEMU reale come uid1000 su file e loop 512/4096 passati, scrittura verificata. Settori logici 4096 richiedono controller NVMe (IDE QEMU li rifiuta), driver stornvme presente in WIM ma guest 4Kn da collaudare.

## Difetto UDF scoperto e stato corrente

IMPORTANTE: scripts/prepare-winre.py è ancora la vecchia versione SBAGLIATA: xorriso importa l'albero ISO9660 tronco e perde UDF, trasformando EFI/Microsoft in EFI/MICROSOF. La vecchia WinRE integrata in config/includes.chroot/opt/ibs/iso/IBS-WinRE.iso non avvia correttamente UEFI (BCD 0xc000000f). NON compilare live con questa copia.

La sorgente originale corretta è .build/winre-overlay/IBS-WinRE-original.iso (originale NAS), da conservare. È UDF 1.02. Ho installato 7zip e genisoimage sul sistema host. Estratta con 7z in .build/winre-udf-source (nomi completi, EFI/Microsoft/Boot/BCD); sostituita sources/boot.wim con .build/winre-overlay/boot.wim; copiati boot images originali in ibs-boot/{bios,uefi}.img.

Comando UDF provato:

genisoimage -udf -iso-level 3 -full-iso9660-filenames -relaxed-filenames -D -N -V CD_ROM -b ibs-boot/bios.img -no-emul-boot -boot-load-size 8 -eltorito-alt-boot -e ibs-boot/uefi.img -no-emul-boot -o .build/WinRE-udf.iso .build/winre-udf-source

Questa ISO ha avviato REALMENTE WinRE UEFI e il componente appunti integrato automaticamente, su disco LOOP passato tramite fdset host_device RW a QEMU uid1000. Prompt WinRE accessibile con Alt+Tab dalla schermata layout tastiera. Boot DVD Windows chiede tasto: usare ritorni durante i primi 35 secondi in TEST, non automatizzare input arbitrari nel prodotto.

## VM / collaudo in esecuzione

Cartella .build/winre-workflow:
- start.py crea fixture sparsa disk.raw da 1 GiB, loop2 (verificare file loop), apre esclusivo RW+probe RO, QEMU uid1000, 2GiB TCG, helper FAT C: con probe.exe. QMP qmp.sock, display Xvfb nel file display, bridge di produzione in processo dedicato (pid in bridge-pid), QEMU pid in pid. Non ci sono dischi fisici reali.
- control.py riusa test-winre-boot.py con WORK diverso. Esempi: python3 .build/winre-workflow/control.py screen / key alt-tab / type '...'. screenshot screen.png.
- probe.c/probe.exe: utility Windows separata che controlla CF_UNICODETEXT ricevuto dal componente di produzione e imposta la risposta Unicode; NON crea un suo canale TCP. Con la prima ISO UDF il test bidirezionale del componente automatico è PASSATO.
- proof.py imposta clipboard X11, avvia C:\probe.exe, poi incolla script LF multilinea che crea X:\gpt-test.txt e lancia DiskPart; verifica GPT/EFI FAT32/MSR/NTFS nel file disk.raw; poi incolla script per scrivere S:\efi-proof.txt e T:\script-proof.txt, controlla marcatori nel disco e Ctrl+A/Ctrl+C verso Linux. Scrive result.json solo se tutto passa.

BUG SCOPERTO: Ctrl+V con testo LF Linux veniva concatenato in una riga dalla console Windows: niente esecuzione! Il proof.py della prima prova è stato terminato (era in attesa GPT). La linea concatenata è ancora nel prompt della VM: cancellarla con ESC, oppure riavviare con nuova ISO.

Ho appena corretto src/clipboard.c: set_clip normalizza LF isolati a CRLF prima di CF_UNICODETEXT; la modalità --test confronta linee normalizzate. Build MinGW -Werror lanciata, helper probe.c aggiornato ad aspettarsi CRLF. WIM .build/winre-overlay/boot.wim aggiornata col nuovo exe e copiata nel tree UDF. Genisoimage sta/ha prodotto .build/WinRE-udf-crlf.iso. Log .build/build-winre-udf-crlf.log e .build/update-clipboard-crlf.log. Verificare completamento e compilazione. Non ancora provata la correzione CRLF.

## Prossimi passi obbligatori

1. Finire prova CRLF: arrestare VM/bridge/Xvfb corrente o cambiare CD via QMP blockdev-change-medium (device ide0-cd0, filename assoluto nuova ISO, format raw, force true), system_reset e premere ritorno a intervalli per il prompt DVD. Se si riavvia VM da zero: chiudere FD prima di staccare SOLTANTO il loop del test, controllando backing file disk.raw. start.py punta ancora alla vecchia ISO di config: cambiarlo alla nuova .build/WinRE-udf-crlf.iso.
2. Il helper FAT tiene snapshot dimensione file: probe.exe è stato ricompilato (CRLF), va copiato in helper PRIMA di nuova VM. Preferire stop e nuova VM con helper aggiornato, ripulire marker ready. Firmware VARS ripristinate da OVMF. Bridge attuale esce su disconnessione del chardev: riavviarlo se si usa reset/nuova VM.
3. Attendere ready, Alt+Tab al Prompt WinRE, eseguire proof.py e ispezionare screenshot/proof.log. GPT EFI NTFS e scritture devono davvero passare, no false dichiarazioni. Provare eventualmente 4Kn con NVMe separatamente. Ripristino di un Windows reale non testabile senza installazione: testare GPT/EFI/scritture, non dire di aver riparato un boot Windows reale.
4. Riscrivere prepare-winre.py usando estrazione UDF con 7z e authoring genisoimage come comando sopra. Conservare originale verificato, non sovrascriverlo con una integrata. Verifica wimverify e BCD completo in UDF. Promuovere soltanto la ISO WinRE integrata collaudata al percorso di config e aggiornare config marker clipboard-integrated.sha256 (ignorato) e assets/WinRE-integrated.sha256.
5. Aggiornare README/VERIFICHE/REQUISITI al risultato ATTUALE: ci sono note vecchie non definitive. Non dichiarare funzionalità della ISO finale prima del collaudo.
6. Collaudare TeamViewer 15.82.6/ordine Rescue e IP overlay nella live: vecchia VM Linux è stata spenta (memoria insufficiente durante caricamento .deb; non usare i vecchi log come prova del nuovo flusso). Servono test grafici su nuova build candidata o ambiente live adeguato. Il collaudo host WinRE completo deve passare PRIMA della compilazione live, come richiesto.
7. Solo dopo prove: compilare una candidata, avviarla, controllare TeamViewer GUI pronto/ID TXT/passwd accettata, overlay IP e Public. Una connessione TeamViewer autenticata da un secondo client NON è stata provata: dirlo chiaramente se rimane così.
8. Commit e push a modifica completa e verificare remoto. Repo https://github.com/emimo69/IBS-RecoveryWin, branch ibs-recoverywin-2.0. Dopo ISO finale funzionante copiare ISO+SHA256 in /mnt/ibs-iso/ISO e verificare SHA256 dalla copia NAS.

## Pulizia

Utente ha tolto ISO fallite dal NAS. Locali 2.0 fallite e .build/previous-iso eliminate. Rimossi duplicati WIM winre-inspect e winre-overlay-vt9zpg_4, vecchia ISO integrata duplicata, clone bare di riferimento e vecchio checkout. Circa 33 GiB liberi al controllo. Chroot/binary/cache servono al lavoro attuale; dopo consegna si può usare lb clean per liberare lo scratch, conservando sorgenti, asset e risultati utili.
