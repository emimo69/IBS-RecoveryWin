# R5 — Piano di collaudo WinRE su QCOW2

Preparato il 26 ottobre 2026. Solo piano: nessun boot WinRE autorizzato
o eseguito da questo documento. Il rapporto del parser è in
[docs/R4D-QEMU-VALIDATION.md](docs/R4D-QEMU-VALIDATION.md).

## Condizioni prima di procedere

1. Ottenere autorizzazione esplicita al boot e identificare la ISO WinRE
   autorizzata, la sua provenienza e il suo SHA-256 atteso. Non usare ISO
   R2/R3 o dischi Windows reali come sostituti. Nessuna build o installazione
   pacchetti implicita nel collaudo.
2. Lavorare come utente non root, soltanto nel progetto. Creare una directory
   privata per la sessione sotto `.build`, registrandone il percorso esatto.
   Tutti gli artefatti scrivibili devono stare lì.
3. Identificare una coppia compatibile di firmware OVMF CODE/VARS reali
   già disponibile nel progetto: architettura x86_64, dimensioni e variante
   corrispondenti. Non utilizzare le fixture sintetiche R4D. Se i firmware
   mancano, fermarsi e concordarne la disponibilità senza cambiare host.
4. Risolvere e controllare tutti i percorsi: file regolari locali, nessun
   device a blocchi/caratteri, symlink ambiguo, mount NAS/USB/Ventoy o
   backing file esterno. Registrare dimensioni, provenienza e hash di CODE,
   VARS modello e ISO. Aprire CODE e ISO in sola lettura; copiare VARS nella
   directory privata e rendere scrivibile esclusivamente la copia.
5. Verificare QEMU/qemu-img disponibili e spazio sufficiente. Controllare
   disponibilità e permessi di `/dev/kvm` senza modificarli; se assente,
   dichiarare TCG e concordarne il limite temporale prima del lancio.
   Non caricare moduli né modificare configurazione host.

## Unico disco guest

Creare una nuova base QCOW2 fittizia, vuota, di dimensione concordata
(proposta: 4 GiB virtuali), senza dati reali e senza backing file.
Verificare formato e integrità con `qemu-img info --output=json` e
`qemu-img check`, registrare hash della base e renderla di sola lettura.
Creare un overlay QCOW2 temporaneo con formato backing esplicito `qcow2`
e percorso assoluto della sola base autorizzata. Controllare l'intera catena
con `qemu-img info --backing-chain --output=json`: esattamente overlay e
base, nessun ulteriore riferimento. Collegare alla VM soltanto l'overlay
come disco scrivibile. La base non va collegata come secondo disco.

## Lancio futuro controllato

Prima del lancio preparare e revisionare l'argv completo e il supervisore.
Usare `-no-user-config -nodefaults`, macchina q35, acceleratore esplicito,
CODE pflash raw `readonly=on`, copia VARS raw scrivibile, ISO come CD-ROM
`readonly=on` con boot da CD, unico disco overlay con formato `qcow2`.
Scegliere un controller disco supportato dalla ISO WinRE autorizzata.
Non riutilizzare launcher con selezione automatica di dischi o media.
Gestire spazi e virgole come verificato dal parser, senza shell interpolata.

Rete disabilitata con `-nic none`, nessuna scheda aggiuntiva, port forwarding,
cartella condivisa, USB/PCI passthrough o percorso `/dev/*` nell'argv dei
backend. Nessun altro disco, fdset di dispositivi o backend implicito.
QMP su socket Unix privato nella directory sessione; eventuale console
grafica soltanto locale, senza listener pubblico. Prevedere avvio con `-S`:
prima di `cont`, controllare via QMP stato fermo, backend, percorsi e flag
RO/RW. Devono comparire solo CODE, copia VARS, CD-ROM ISO e disco overlay.

Supervisore con limite totale di 10 minuti incluso il boot. Alla scadenza
o a un errore inviare QMP `quit`; attendere al massimo 10 secondi, poi
terminare il processo, attendere 5 secondi e infine kill/reap se necessario.
Gestire anche interruzione utente e fallimento della console/QMP con cleanup
garantito. Non lasciare processi QEMU in background.

## Osservazioni e punti di stop

- Annotare boot OVMF reale e raggiungimento dell'interfaccia WinRE come
  risultati distinti. Firmware sintetico o CPU ferma non soddisfano il boot.
- In WinRE elencare i dischi e verificare presenza di un solo disco virtuale
  con dimensione concordata; il CD-ROM è un supporto separato. Non eseguire
  installazione Windows, riparazione automatica, formattazione o ripristino.
- Fermarsi se compare un backend inatteso, un supporto fisico, rete attiva,
  base/ISO/CODE scrivibile, catena diversa da quella verificata, errore
  firmware, richiesta di usare dati reali o mancato boot entro il timeout.
- Qualsiasi prova di scrittura/ripristino sulla fixture richiede un incarico
  successivo esplicito. NAS, USB, Ventoy e Windows reale restano esclusi.

## Chiusura e criteri di accettazione

Dopo arresto e reap di QEMU, confrontare SHA-256 di base, ISO, CODE e VARS
modello con quelli iniziali: devono essere invariati. La copia VARS e
l'overlay possono cambiare. Verificare offline l'overlay con qemu-img;
conservare un rapporto senza credenziali con versioni, argv, backend QMP,
tempi, esiti e limiti. Se gli hash differiscono, riportare il fallimento e
fermare ogni ulteriore prova.

Rimuovere soltanto socket, copia VARS, overlay e base fittizia creati per
questa sessione, dopo verifica dei percorsi e chiusura dei processi; oppure
conservarli esplicitamente per diagnosi, registrandolo. Mai cancellare
firmware originali, ISO, fixture precedenti o file di altri task.

Accettazione: boot OVMF osservato, WinRE raggiunto, unico disco virtuale
riconosciuto, rete assente, backend conformi, hash protetti invariati,
processo terminato e cleanup documentato. Ciò non dimostra recupero dati,
avvio Windows, TeamViewer/SSH né compatibilità con dischi reali.
