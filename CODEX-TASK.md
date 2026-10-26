# IBS-RecoveryWin R4 — proseguimento sviluppo dopo collaudo timer

ESEGUI L'INCARICO. Il timer unattended è stato collaudato con success su un task di sola lettura. Questa volta il task è di sviluppo software. Leggi AGENTS.md prima di tutto.

Contesto: ISO R3 già compilata e testata con Live QEMU, SSH, TeamViewer, indicatore IP e launcher. R2/R3 sono basi da conservare. La R4 era stata interrotta per priorità timer; nei precedenti tentativi un possibile problema di quoting di argomenti OVMF con virgole è stato scoperto, ma NON corretto per sandbox read-only. Riprendi dalla situazione effettiva di file e commit, non supporre che il fix sia già presente.

1. Esamina i moduli QEMU/OVMF, selezione ISO NAS/Ventoy, i file media.py e vm.py, launcher Monta ISO e Avvia OS, e relativi test. Riproduci e correggi il problema di escaping di virgole nei parametri QEMU che includono percorsi OVMF; verifica spazi e caratteri speciali nei percorsi. Aggiungi test di regressione ripetibili.
2. Esegui test statici/mocks non distruttivi per ISO WinRE/Acronis, UEFI, Legacy, isolamento del disco Live e protezioni contro scritture involontarie ai dischi fisici. Non affermare che WinRE o Windows siano avviabili finché non esiste test reale documentato.
3. Mantieni funzionanti SSH, TeamViewer, IP desktop e launcher. Non alterare le ISO R2 e R3 o cache; non avviare build ISO senza necessità ed esplicita autorizzazione. Non usare NAS/USB/dischi reali del server durante prove. Non fare operazioni su disco fisico o credenziali.
4. Esegui i test disponibili e verifica la configurazione. Commit/push su ibs-recoverywin-1.0 in piccoli gruppi, senza --force. Se sandbox impedisce push, non aggirarla: conserva e segnala con precisione il blocco.
5. Produce un documento docs/R4-PROGRESS.md con prove realmente effettuate, difetti corretti e ciò che manca (compresa la prova boot WinRE reale). Non fare claim inventati.
6. Non modificare timer, servizio systemd o CODEX-TASK.md. Evita sessioni Codex parallele. Procedi autonomamente sui controlli consentiti fino al completamento di R4 statica, poi fermati.

Priorità: robustezza QEMU/WinRE, verifiche riproducibili, nessuna regressione R3.
