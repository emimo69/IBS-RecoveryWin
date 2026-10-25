# CODEX-TASK.md — Incarico esecutivo 2026-10-25: TeamViewer affidabile e preparazione primo test virtuale

**Quando ricevi «Leggi CODEX-TASK.md», ESEGUI quanto segue**, non limitarti a riassumere. Leggi AGENTS.md. Lavora esclusivamente nel ramo `ibs-recoverywin-1.0`, cartella `/opt/ibs-recoverywin-1.0`. La versione precedente dell'incarico è conclusa. Verifica lo stato Git all'inizio e non sovrascrivere modifiche locali.

## Priorità 1 — correggere due difetti REALI in TeamViewer
1. Nel file `config/includes.chroot/usr/local/sbin/ibs-remote`, rendi rigorosa l'estrazione dell'ID di `teamviewer info`: non accettare prefissi numerici con altro testo e non considerare ID valido in caso di comando fallito. Gestisci esplicitamente il codice di uscita del comando, senza far fallire prematuramente lo script sotto `set -e`. Scegli un parsing tollerante per i formati concreti di TeamViewer CLI, e documenta quanto non collaudabile staticamente.
2. Implementa un gestore EXIT/errore che, in caso di uscita imprevista, sostituisca `/mnt/teamviewer.txt` (stesso percorso obbligatorio) con un messaggio chiaro di errore, non lasci «inizializzazione in corso» all'infinito e non pubblichi password non realmente impostate. Conserva scrittura atomica e accessibilità a `admin`. Nessun contenuto delle credenziali nei log.
3. Conserva tutte le funzioni già previste: utente e login `admin/admin`, SSH, TeamViewer automatico, ID/password/IP reali nel file, Conky, icona XFCE che apre Mousepad. Non cambiare il percorso del TXT e non introdurre altri requisiti.
4. Aggiungi test statici e, se fattibile senza daemon, test unitari con comandi `teamviewer` simulati per successo, info non valido, errore inatteso e assenza IP; niente file reali /mnt/teamviewer.txt nei test. Esegui i test.

## Priorità 2 — preflight prima del collaudo
5. Verifica gli script `live-build` (boot username=admin, installazione dei pacchetti, setup SSH, TeamViewer, launchers, live-config). Prepara soltanto le correzioni indispensabili e controlli preflight. Segnala dipendenze che impedirebbero avvio.
6. Prepara una guida BREVE di test QEMU della Live, separata da un'immagine Windows su QCOW2 da 64GB già presente in `/opt/ibs-recoverywin-test/windows11-test.qcow2`. Non collegare mai direttamente dischi fisici; non dare per testate funzioni non avviate. Verifica eventuale possibilità di nested KVM prima di pianificare QEMU dentro QEMU, senza farlo partire in questa fase.

## Salvataggio e controllo
7. Commit e push su GitHub **dopo la priorità 1**, poi un secondo commit/push per la priorità 2. Verifica ogni push e l'hash remoto corrispondente. Se push non possibile, fermati e segnala.
8. Lascia il timer così com'è: è attivo sul server, controlla GitHub, ma NON esegue Codex automaticamente. Non modificare il timer in questo incarico.

**VIETATO compilare ISO, installare o avviare VM, cancellare dati, montare/modificare dischi fisici, intervenire su altri progetti o rami.**
