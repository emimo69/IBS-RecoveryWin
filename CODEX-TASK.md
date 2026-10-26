# IBS-RecoveryWin — avanzamento R4, QEMU/WinRE e fonti ISO (senza dischi fisici)

Leggi AGENTS.md; esegui questo incarico limitato al progetto e ramo ibs-recoverywin-1.0. La R3 è base stabile: preservare integralmente R2/R3 e cache. Questa attività deve poter essere svolta anche in sessione interattiva mentre il timer unattended è in diagnosi. Non toccare script dell'automazione, stato del timer, CODEX-AUTOSTART-TASK.md, altri progetti, dati/credenziali o dischi fisici.

1. Esamina i launcher "Monta ISO" e "Avvia OS", i moduli media.py e vm.py e i test relativi. Fai verifiche statiche e mock non distruttivi su selezione ISO NAS/Ventoy, quoting dei percorsi contenenti spazi, avvio CD-ROM UEFI OVMF/Legacy e isolamento del disco base. Testa che nessuna opzione possa aprire disco reale in scrittura per errore e che Ventoy/Live siano esclusi.
2. Verifica presenza di pacchetti, OVMF, qemu-system, qemu-img, GUI, e gestione errore in assenza di /dev/kvm. Non dichiarare boot WinRE/Windows riuscito finché non c'è una prova reale su hardware adatto. Non montare NAS né chiavetta reali nel server di sviluppo.
3. Risolvi SOLO difetti riproducibili con test in ambiente mock/immagini fittizie. Aggiungi regressioni mirate. Non avviare Windows su disco fisico e non collegare il QCOW2 Windows test reale.
4. Verifica che gli script del desktop, i servizi SSH/TeamViewer e l'indicatore IP non vengano alterati; nessuna nuova build ISO senza motivo, e non sovrascrivere vecchie ISO.
5. Esegui test disponibili, commit e push per gruppi piccoli, senza force; se la sandbox impedisce commit/push, non inventare successo: registra esattamente l'ostacolo. Non tentare di aggirare la sandbox o elevare i privilegi. Conserva tutti i cambiamenti e non ripetere lavori conclusi.

Obiettivo: rendere robusta la prossima fase WinRE/QEMU con prove statiche misurabili senza causare regressioni.
