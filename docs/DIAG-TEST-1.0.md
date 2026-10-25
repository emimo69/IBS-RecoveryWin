# Diagnosi dei guasti TEST-1.0

Cause verificate prima di autorizzare operativamente la nuova build. Diagnosi iniziale
sulla ISO originale invariata in QEMU TCG, senza dischi, SSH admin/admin riuscito.
Il daemon avviato separatamente restituisce exit code 0 e stato active.
L'avvio di ibs-remote invece riproduce il fallimento e lo stop del daemon.

Causa verificabile: nel pacchetto TeamViewer 15.82.6, funzione SetPasswd in
/opt/teamviewer/tv_bin/script/tvw_extra, `teamviewer passwd` esegue stop e start
del daemon. Il nostro script esegue inoltre un restart dopo la prima accettazione
licenza. `Requires=teamviewerd.service` propaga lo stop a ibs-remote e interrompe
la configurazione stessa. I soli eventi systemd filtrati mostrano questa
sequenza di avvii, fallimenti IBS e stop del daemon; nessun ID/password acquisito.

Correzione minima: usare Wants per avviare il daemon e mantenere After per
l'ordine, senza propagare lo stop richiesto dalla CLI. Nessuna modifica a
admin/admin, SSH o contenuto/percorso TXT. La [semantica di systemd](https://www.freedesktop.org/software/systemd/man/latest/systemd.unit.html)
conferma la propagazione di stop/restart di Requires.

`python3 scripts/test-remote.py` include una regressione sulla relazione tra
unità (Wants e After presenti; Requires/BindsTo/PartOf assenti). I test CLI
restano simulati e non dimostrano connettività TeamViewer reale.

## Diagnosi ripetibile, solo dentro il guest

Invocare `python3 scripts/diagnose-live.py` come admin nella Live. Lo script
rifiuta il server privo di boot=live; fornisce solo stati/exit code, indicatori
XDG/sessione, presenza/eseguibilità file e categorie fisse di eventi systemd.
Non legge il TXT, non invoca teamviewer info e non stampa log grezzi.
I journal sono filtrati nel guest in memoria e non copiati sul server/GitHub.

Probe opzionali, da usare soltanto nella VM temporanea senza dischi:
`--probe-launcher` prova il launcher nell'ambiente della sessione XFCE;
`--probe-services` tenta avvio separato daemon e riprova ibs-remote;
`--probe-dependency-fix` prova la sostituzione Requires→Wants nell'unità del
solo guest e ricontrolla gli stati. I probe modificano solo la sessione RAM
del guest, non sono attivati dal task watcher e non devono essere eseguiti
sul server di sviluppo.

## Launcher: falso negativo del test precedente

Secondo avvio della stessa ISO, attesa la sessione XFCE admin e altri 25 secondi:
XDG risolve Scrivania, directory/configurazione presenti, launcher già presente
ed eseguibile **prima** del probe manuale. Il probe nell'ambiente XFCE, con
DISPLAY e bus di sessione presenti, termina con exit code 0 senza errori di
permessi o metadati. Non è necessaria alcuna modifica al launcher funzionante.
Il precedente test verificava il desktop troppo presto dopo il primo SSH.

Corretto il controllo in scripts/test-live-qemu.py: attende prima la sessione
XFCE, poi autostart e stato definitivo di ibs-remote. Lo script riceve una ISO
all'interno del progetto, avvia solo CD-ROM/TCG senza dischi e spegne la VM
nel finally; è uno strumento di test manuale, non viene invocato dal timer.
`python3 scripts/test-launcher.py` verifica con HOME isolata Scrivania,
percorso personalizzato con spazi, ritardo GVFS, modo 0755, checksum e comando
Mousepad sul percorso corretto; non legge il TXT reale o avvia una GUI.

La nuova build è stata eseguita in .build/TEST-1.0-R2-build con copia dei sorgenti
config e cache condivisa via collegamento alla cache esistente. Nessuna pulizia
chroot/binary o cancellazione/sovrascrittura di ISO precedente: il vecchio albero
di build e le due ISO originali restano intatti. L'unica modifica funzionale
alla Live è la dipendenza Wants della preparazione TeamViewer.

## Conferma dopo la build

La R2 conferma teamviewerd active/running e ibs-remote active/exited con exit 0;
launcher presente, eseguibile e checksum di attendibilità corretto. Il probe
`--probe-launcher` prova anche l'Exec Mousepad con output soppresso, senza
screenshot o acquisizione del TXT. Risultati, hash e limiti nel
[rapporto R2](TEST-1.0-R2-RESULTS.md).
