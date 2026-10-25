# Ripristino sicuro dopo push non-fast-forward durante R3

ESEGUI questo incarico su richiesta. Progetto esclusivo /opt/ibs-recoverywin-1.0, ramo ibs-recoverywin-1.0.

Situazione osservata: Codex ha quattro commit R3 già pubblicati, ma una correzione locale Ventoy (commit locale riportato come 1d6f34b) non è stata pubblicata perché origin è avanzato. La build R3 è stata interrotta (exit 143). R2 e cache devono restare intatte.

1. Prima ispeziona stato repo, branch, commit locale, commit remoto, eventuali processi lb/build in corso e spazio disponibile. Non avviare altre build finché non hai riconciliato Git.
2. Salva senza perdere modifiche locali. Usa git fetch e confronto log/merge-base. Se la working tree è pulita e i commit sono divergenti, integra i commit remoti con procedura conservativa (rebase/cherry-pick in una working tree isolata o merge controllato). NON usare push --force, reset --hard, clean -fd, cancellazioni o riscrivere altri commit. Se ci sono conflitti, risolvili controllando i contenuti sorgenti e verifica test regressione; se rischioso, fermati con spiegazione.
3. Non cambiare CODEX-TASK.md, CODEX-AUTOSTART-TASK.md e non sovrascrivere incarichi su GitHub. Proteggi R2 e tutte le ISO/test precedenti, cache e NAS/USB/dischi reali.
4. Esegui test mirati sulla correzione permessi Ventoy, selezione ISO e QEMU senza dischi fisici. Quando Git è riconciliato, commit/push normale e verifica sha remoto identico. Non pubblicare credenziali o contenuti TeamViewer.
5. Soltanto dopo riconciliazione completata, riprendi eventuale build R3 in percorso isolato, se la quota Codex e lo stato build lo consentono. Non duplicare processi e non cancellare cache. Se quota in esaurimento, conserva checkpoint e documenta i prossimi passi.
6. Restituisci stato preciso: push riuscito sì/no, compile R3 sì/no, ISO prodotta sì/no e prove realmente eseguite.
7. Non implementare ora il runner unattended mentre la R3 è in corso; è un incarico separato.

Il proprietario ha chiesto di ridurre interventi manuali. Lavora entro sandbox e autorizzazioni disponibili, senza elevare permessi o toccare dischi reali.
