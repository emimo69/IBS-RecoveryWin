# Primo collaudo virtuale della sola Live

Guida preparata, **comandi QEMU non eseguiti**. Prima servono autorizzazione
separata alla compilazione ISO e all'avvio della VM. Nessun componente QEMU
viene aggiunto nella Live. Non installare pacchetti in questa fase.

## Preflight rilevato il 25 ottobre 2026

`python3 scripts/preflight-live.py --host` è passato. Disponibili live-build,
QEMU e SSH; i nomi dei pacchetti sono nei metadati APT locali. Non è una prova
di risoluzione completa delle dipendenze o disponibilità dei server remoti.
L'ordine live-build locale copia gli includes dopo i pacchetti e prima degli
hook: l'unità ibs-remote è quindi disponibile quando l'hook la abilita.
Gli hook collegati risultano presenti sull'attuale host; su un altro host
occorre ricontrollare compatibilità e versione di live-build.

`live-config` 11.0.5 raccomanda `user-setup`: la configurazione mantiene
`LB_APT_RECOMMENDS=true`. Disabilitarlo senza aggiungere esplicitamente
user-setup impedirebbe la creazione dell'utente. Il componente personalizzato
0990 viene dopo 0030-user-setup e imposta admin/admin, sudo e chiavi SSH.
Il frammento sshd abilita la password per admin; la configurazione effettiva
va comunque verificata al boot con `sudo sshd -T`.

Il download HTTPS del pacchetto TeamViewer corrente e `apt-get install`
restano dipendenze esterne non collaudate. Eventuali incompatibilità amd64,
dipendenze, licenza o formato CLI non supportati devono fermare build/test.
Il preflight non dichiara TeamViewer né SSH operativi. Nessuna correzione
aggiuntiva ai componenti Live è risultata indispensabile dall'analisi statica.

CPU esposta: QEMU Virtual CPU, hypervisor KVM; **vmx/svm assenti**,
**/dev/kvm assente**, parametri nested dei moduli Intel/AMD assenti.
Nested KVM non disponibile con la configurazione esposta: non usare
`-enable-kvm`, non caricare moduli o cambiare host. Un futuro cambio richiede
nuova verifica di CPU esposta, /dev/kvm e permessi. Non pianificare QEMU dentro
la Live: per questo primo test basta QEMU sul server con TCG, più lento.

## Avvio futuro, solo dopo autorizzazione

Esempio da eseguire come utente non root dalla directory del progetto, con
ISO già compilata e verificata. Sostituire il nome ISO se diverso:

```sh
qemu-system-x86_64 -no-user-config \
  -name IBS-RecoveryWin-live-test -accel tcg -cpu max -smp 2 -m 4096 \
  -cdrom /opt/ibs-recoverywin-1.0/live-image-amd64.hybrid.iso -boot order=d \
  -nic user,model=virtio-net-pci,hostfwd=tcp:127.0.0.1:2222-:22 \
  -display vnc=127.0.0.1:1
```

La VM ha solo ISO e RAM, nessun disco dati. Nessun `/dev/sd*`, `/dev/nvme*`,
mount o passthrough. Il file `/opt/ibs-recoverywin-test/windows11-test.qcow2`
(64 GB indicati nell'incarico) **resta separato e non viene collegato**:
non è stato aperto, ispezionato o modificato. Non avviare Windows né una VM
annidata. La rete user-mode espone SSH solo su localhost:2222; VNC solo su
localhost:5901. Da remoto usare un tunnel SSH verso il server di sviluppo.

## Criteri del primo test

1. Verificare boot, autologin admin, XFCE italiano e tastiera italiana;
   controllare `id`, `locale` e `timedatectl`. Provare login con admin/admin.
2. Verificare `systemctl is-active ssh teamviewerd ibs-remote`, configurazione
   effettiva SSH e login da host con `ssh -p 2222 admin@127.0.0.1`.
3. Aprire l'icona **TeamViewer ID e Password**: Mousepad deve aprire il TXT
   senza sudo o richiesta di attendibilità. Controllare proprietario e modo
   con `stat -c '%U:%G %a' /mnt/teamviewer.txt`: atteso root:admin 640.
4. Confrontare privatamente ID/password/IP con la sessione; provare una vera
   connessione TeamViewer da un secondo dispositivo. Non allegare credenziali,
   contenuto TXT o screenshot con password a log/GitHub.
5. Verificare anche Conky, rete assente (messaggio senza credenziali pronte),
   riavvio della VM e rigenerazione delle credenziali. Annotare esiti senza
   segreti. Arrestare la Live normalmente; non installare nulla su dischi.

Riferimenti: [dipendenze live-config Trixie](https://packages.debian.org/trixie/live-config),
[componenti live-config 11.0.5](https://sources.debian.org/src/live-config/11.0.5/components/),
[opzioni QEMU ufficiali](https://www.qemu.org/docs/master/system/qemu-manpage.html).
