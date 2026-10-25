# IBS-RecoveryWin 0.2: correzioni e verifica

Il ramo `fix/ibs-recoverywin-0.2` applica le priorità di `AGENTS.md`.
L'issue #1 non è stata leggibile nell'ambiente: API/GraphQL GitHub 403,
pagina web 404. Il confronto con il suo testo resta necessario prima della revisione finale.
Nessuna ISO è stata compilata e nessun disco reale è stato usato per i test.

## Diagnosi e modifiche

| Percorso | Problema riscontrato | Correzione |
| --- | --- | --- |
| `ibs-qemu-launcher`, `ibs-qemu-disk-{session,direct}` | `pkexec` ripulisce DISPLAY/XAUTHORITY; gli errori non erano visibili da XFCE | Policy per eseguibili fissi, autorità X esportata dal launcher, verifica della sessione ed errori mostrati all'utente. Regola polkit IBS antecedente alla regola permissiva di live-config. |
| `ibs-qemu-disk-safe` | Uscita incondizionata prima del codice di protezione | Alias al percorso protetto unico, senza fallback a scrittura diretta. |
| `ibs-disk-select`, `ibs-disk-check` | Filtri diversi, NBD/zero byte accettabili, stack DM non montati non esclusi | Policy comune, soli dischi fisici interi, capacità positiva, esclusione USB/rimovibili/RO/stack e membri RAID/LVM/cifrati/ZFS. Rivalidazione privilegiata e identità prima dell'apertura. |
| `ibs-qemu-disk-direct` | Lock dentro directory casuale: non esclude altre VM; consenso solo prima di pkexec | Lock root condiviso per major/minor, ulteriore conferma con identità lato root, file descriptor ereditato per fissare il device aperto. |
| `ibs-disk-readonly`, `ibs-qemu-disk-session` | La protezione non aveva una verifica esplicita del flag RO | Mapping DM `--readonly` e verifica `blockdev --getro`; scritture della VM solo su qcow2 temporaneo; rimozione del solo mapping IBS di sessione. |
| `ibs-qemu-preflight`, `ibs-qemu-firmware` | OVMF richiesto anche per legacy, VARS non controllato, virgole nei percorsi | Controlli distinti per modalità; CODE e VARS richiesti solo per UEFI; copia VARS privata; escaping dei percorsi per QEMU. |
| `ibs-ventoy-iso-mount`, `ibs-iso-select` | Mount può fallire per il mapper del boot; percorso USB terminato da `\\n` letterale; NAS predefinito | Tentativo RO e fallback loop RO di proprietà della sessione, senza toccare il mapper Live; newline corretto; selezione file locale senza NAS; timeout NAS. |
| `ibs-qemu-iso` | Riavvii WinRE non osservabili, VARS temporanee non rimosse, KVM scelto per sola esistenza | `-no-reboot`, menu firmware, stderr in log persistente della sessione utente, pulizia VARS, verifica accessibilità KVM. Non dimostra la causa del reboot WinRE. |
| Locale e XFCE | Nessuna configurazione italiana nei sorgenti presenti; launcher non marcati attendibili | Locale generato, tastiera IT, Europe/Rome, impostazioni live-config, attendibilità dei soli launcher IBS nella sessione GVfs utente. |
| SSH | OpenSSH presente senza un flusso di provisioning sicuro per PuTTY | Servizio inizialmente disabilitato; helper con conferma, chiave pubblica OpenSSH, fingerprint, utente non root e IP/CIDR obbligatorio. Password/root login vietati, nessuna credenziale incorporata. |
| `ibs-windows-repair`, launcher Ripara Windows | Il launcher avviava soltanto una ISO | Selezione disco GPT, individuazione Windows mediante mount NTFS RO/norecover, scelta Windows/ESP, backup EFI su supporto esterno e SHA256. Produce una guida WinRE riferita all'analisi eseguita. |

## Uso e limiti operativi

Lanciare QEMU dal desktop XFCE attivo, con l'agente polkit disponibile.
Le azioni IBS richiedono autenticazione amministrativa; non usare `xhost +` o
regole che autorizzino globalmente pkexec. Configurare le credenziali locali prima
della distribuzione; l'accesso SSH non utilizza le password predefinite della Live.
La modalità diretta può modificare il disco reale e richiede conferma separata.
La modalità protetta conserva i file originali e scarta l'overlay al termine.
Servono 20 GiB liberi su destinazione persistente separata; il NAS è opzionale.

Per PuTTY: aprire **Configura SSH per PuTTY**, specificare IP/CIDR del tecnico,
incollare la chiave pubblica OpenSSH esportata da PuTTYgen e confermare il fingerprint.
Usare in PuTTY la chiave privata corrispondente. Non incollare chiavi private.
L'helper limita le sorgenti con `AllowUsers utente@rete`, abilita solo il gruppo
`ibs-remote` e valida sshd prima dell'avvio. Per spegnerlo:
`sudo systemctl stop ssh.service`. Non apre porte del router né configura VPN;
fuori sede occorre connettività già disponibile o VPN gestita separatamente.
Le chiavi host vengono generate sulla Live; verificare il fingerprint host prima
alla connessione, senza affidarsi a chiavi host incorporate nell'immagine.

**Ripara Windows** esegue analisi e backup, non un `bcdboot` automatico da Linux.
Il backup include `efi.tar`, `SHA256SUMS`, `analisi.txt` e `WinRE.txt`.
I mount Windows/EFI sono in sola lettura. Per modificare BCD avviare WinRE sul disco
selezionato, verificare nuovamente disco/volumi/lettere, quindi seguire WinRE.txt
con consenso esplicito. L'avvio di una ISO dal launcher ISO non collega il disco
fisico: non considerarlo una riparazione del disco selezionato. L'integrazione
automatica di ISO WinRE + disco scelto rimane da definire e revisionare.
BitLocker, volumi NTFS ibernati/non leggibili, dischi USB e MBR sono esclusi da
questa procedura. Non vengono eseguiti `clean`, `format` o riparazioni NTFS.
Il selettore di destinazione del backup riusa il vincolo conservativo di 20 GiB.

## Verifiche riproducibili senza ISO

```sh
bash tests/check.sh
# Se ShellCheck è stato estratto fuori dal repository:
SHELLCHECK=/workspace/ibs-tools/shellcheck/usr/bin/shellcheck bash tests/check.sh
```

La suite usa Python standard library e Bash. Copre sintassi degli script,
policy disco, holder DM, montaggi/swap, rifiuto dei normali file come device,
percorsi Ventoy con spazi, fallback senza NAS e cleanup del loop fallito,
annullamento, policy polkit, errori privilegi/sessione grafica, blocco condiviso
fra modalità protetta e diretta, cambio identità e argv/errori/cleanup del launcher ISO.
I confini OS/dispositivo sono simulati esplicitamente: non si creano block device,
non si montano filesystem e non si avviano VM nei test.
ShellCheck 0.10.0 è passato sugli script modificati/nuovi. Gli script invariati
`ibs-teamviewer-auto` e `ibs-iso-list` hanno warning preesistenti sulle variabili
inutilizzate; il controllo opzionale non li include.
I nomi delle variabili live-config sono stati confrontati con il pacchetto Debian
trixie live-config 11.0.5, senza eseguirne i componenti nell'host cloud.

Restano da verificare sulla Live, dopo revisione e autorizzazione della build:
GUI/polkit e launcher attendibili, effettiva non scrivibilità del backing DM,
accesso SSH con chiave e rifiuto di password/root/reti estranee, USB Ventoy reale,
boot WinRE UEFI/legacy e una riparazione BCD su disco di prova sacrificabile.
Non è dichiarato il funzionamento su macchina fisica né risolto il reboot WinRE.
