# Diagnosi dei guasti TEST-1.0

Prima ricompilazione sospesa fino alla verifica delle cause. Diagnosi iniziale
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

## Launcher: verifica ancora in corso

La prima diagnosi ha trovato SSH pronto prima di XFCE, directory desktop e
configurazione XDG non ancora presenti. Questo non basta per attribuire un
difetto al launcher: il controllo viene ripetuto dopo attesa della sessione
XFCE e dell'autostart, sulla stessa ISO, senza build alla cieca.
