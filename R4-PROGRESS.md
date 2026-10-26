# R4C — convalida software e rapporto aggiornato

R4B validata nei test statici; avvio reale WinRE/Windows e NAS/USB non collaudati.

## Verifiche reali del 26 ottobre 2026

- Checkout inizialmente pulita, HEAD `00a570f`; commit locale `8982d22` presente. Il diff di quest’ultimo modifica solo le due righe OVMF in vm.py con `replace(',', ',,')`, aggiunge il test OVMF e aggiorna il rapporto. Nessun test originale eliminato; patch R4B non riapplicata.
- `python3 -B scripts/test-vm.py`: PASS, 9 test, incluso CODE/VARS con spazi, virgole singole e consecutive; backing readonly, overlay, esclusione Live/Ventoy e conferma errata prima di apertura dispositivo.
- `python3 -B scripts/test-media.py`: PASS, 7 test; fixture Ventoy e mount mock readonly, percorsi speciali, token obsoleti, permessi di attraversamento e configurazione NAS statica.
- `python3 -B scripts/test-r4-paths.py`: PASS, 3 nuovi test ripetibili, senza montaggi, rete o processi QEMU. Selezione GUI Monta ISO da NAS e Ventoy con fixture WinRE/Acronis, spazi/virgole/Unicode e assenza Ventoy; rifiuto backend di ISO esterne e symlink verso l’esterno, file mancante, WinRE senza KVM, Acronis senza consenso TCG e Avvia OS senza KVM, prima di qualsiasi apertura o avvio; mount NAS simulato e rifiuto risposta findmnt scrivibile.
- `bash scripts/verify-config.sh`: PASS; controlli statici configurazione, sintassi, launcher e `git diff --check`. Nessuna build.

## Analisi statica e limiti

La GUI passa percorsi come argomenti distinti e il helper restituisce gli errori previsti in JSON; OSError e ValueError sono gestiti. Il backend risolve il percorso prima di verificare estensione, esistenza e appartenenza a MEDIA_ROOT; il grafo QEMU usa JSON per i percorsi overlay e fd readonly per la base protetta. Nessun difetto nuovo comprovato richiede una modifica al codice operativo.

Il controllo backend ammette qualunque ISO sotto MEDIA_ROOT, non vincola la richiesta alla sola sottocartella NAS/Ventoy appena selezionata nella GUI. Il messaggio “sorgente ... selezionata” è più specifico del controllo effettivo: questo limite resta documentato, senza attribuire isolamento tra sorgenti non verificato. Il riconoscimento WinRE senza KVM dipende dal nome contenente “winre”; Acronis è trattata come ISO generica e il consenso TCG non ne prova la compatibilità.

Non collaudati: parser QEMU reale con OVMF, avvio WinRE/Windows/Acronis, sessione grafica Live, KVM, NAS/USB reali e connessione remota esterna. Il processo runner terminato con successo dimostra solo l’esito dei comandi software sopra riportati.

## Pubblicazione impedita nell’ambiente corrente

`git ls-remote origin HEAD refs/heads/main refs/heads/master` fallisce: `Could not resolve host: github.com`. Non è stato quindi possibile verificare il contenuto corrente su GitHub né confermare la pubblicazione remota del commit OVMF; la sua presenza è comprovata solo nella checkout locale.

`findmnt -T .git -n -o TARGET,VFS-OPTIONS` mostra `.git` con opzione `ro`. Commit vietato dal filesystem corrente: non tentato, senza ripetere procedure già fallite né modificare permessi. Push non tentato. R4C non è conclusa né pubblicata. Patch locale `R4C-review.patch` fuori dai sorgenti, contenente questo rapporto e il nuovo test, per revisione nella shell host autorizzata.

## Prossimi passi

1. Dalla shell host con repository scrivibile e rete disponibile, verificare GitHub e il diff locale, rieseguire i tre script test e verify-config, quindi commit e push delle sole modifiche R4C e verifica dell’hash remoto sul branch `ibs-recoverywin-1.0`. Fermarsi se il push fallisce.
2. Con autorizzazione specifica, predisporre un successivo test WinRE con ISO selezionata e fixture virtuali, registrando firmware, disponibilità KVM, log e risultato osservabile. Il parser e l’avvio reale restano da verificare.
3. Mantenere NAS/USB e dischi fisici fuori dal collaudo corrente. Nessuna modifica a timer, servizi, CODEX-TASK.md, ISO R2/R3, cache, utenti o altri progetti; nessuna build ISO eseguita.
