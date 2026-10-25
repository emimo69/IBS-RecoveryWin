# CODEX-TASK.md — NUOVO INCARICO: diagnosticare e correggere i due guasti del primo test ISO

**ESEGUI** quando leggi questo file tramite Codex. Leggi AGENTS.md. Opera solo su /opt/ibs-recoverywin-1.0, ramo ibs-recoverywin-1.0. Non riscrivere componenti funzionanti e non intervenire su vecchie versioni.

## Risultati reali già acquisiti
Leggi prima docs/TEST-1.0-RESULTS.md (test QEMU completato). ISO compilata correttamente. Debian Live avviata; SSH admin/admin OK, locale italiano OK, XFCE in esecuzione. TXT /mnt/teamviewer.txt esiste ed è leggibile root:admin 0640. **Problemi: teamviewerd inattivo, ibs-remote failed status=1, launcher desktop non trovato eseguibile.** GUI e TeamViewer remoto non ancora verificati. Niente dischi collegati.

## Lavoro richiesto, in ordine
1. **Diagnosi accurata senza build**: confronta gli script e le unità systemd già pubblicate con i risultati. Individua difetti verificabili. Prepara un sistema di diagnosi per la Live di test già esistente, acquisendo solo stati/exit code e messaggi filtrati senza trascrivere credenziali TeamViewer; eventuali log completi devono restare locali, mai su GitHub. Il server di sviluppo non deve essere confuso col guest.
2. **TeamViewer daemon**: controlla ordine/condizioni d'avvio e gestione del servizio nella Live. Non considerare avvio automatico riuscito perché è stato fatto systemctl enable nel chroot. Individua causa prima di cambiare e correggi solo gli errori confermati. Assicurati che /mnt/teamviewer.txt, al completamento, contenga soltanto ID e password reali, oltre all'IP se già previsto. Se non pronti, messaggio breve senza credenziali fittizie. Non cambiare admin/admin né SSH.
3. **Launcher desktop**: verifica che il processo autostart venga eseguito nell'ambiente XFCE admin, che xdg-user-dir DESKTOP sia corretto con locale italiano, che il .desktop sia copiato e attendibile/eseguibile, e che Exec=mousepad /mnt/teamviewer.txt funzioni. Correggi soltanto quanto necessario.
4. Test automatici dei difetti e regressione: statici/mocks per TeamViewer e launcher, preflight; nessun test spacciato per connettività reale. Commit/push separati per fix accertati; verifica hash remoto.
5. **Solo quando risolti nei sorgenti i problemi accertati**, puoi compilare UNA nuova ISO di TEST, preservando integralmente ISO precedente e cache; non usare clean --purge; non sovrascrivere la precedente ISO. Prova solo la Live senza dischi in QEMU TCG come nel test precedente, con timeout e spegnimento. Verifica SSH, stato teamviewerd, ibs-remote, presenza permessi/launcher; non leggere né pubblicare ID/password reali. Confronta con i risultati precedenti e documenta SHA256 e limiti del test. Se non puoi diagnosticare realmente senza dati della Live, NON ricompilare alla cieca: documenta blocker e modalità per ricavare solo dati indispensabili con minima interazione.
6. Salva sorgenti, test e report su GitHub con commit e push frequenti. Non committare ISO, file credenziali, log con dati personali, o sessioni TeamViewer.

**MAI modificare dischi fisici, usare il QCOW2 Windows da 64 GB, cancellare ISO o altri progetti, cambiare proprietari di cartelle del server, modificare timer.**
