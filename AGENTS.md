# IBS-RecoveryWin 2.1 Codex
Lavorare soltanto nella copia separata della candidata Codex. Non modificare la ISO corrente, il progetto 2.0, la 1.0 o altri progetti IBS.
L’utente ha autorizzato WinRE ad accedere in lettura e scrittura ai dischi fisici selezionati. I test di sviluppo devono usare esclusivamente dischi virtuali; escludere dischi montati, swap e supporto della live. Non compilare ISO senza autorizzazione esplicita.
Dopo ogni modifica completa eseguire commit e push soltanto su develop, verificando il remoto; non modificare main e fermarsi se il push fallisce.
Non dichiarare operative funzionalità senza prove reali nella live.
Non copiare autenticazioni personali dalla Live nel progetto o nella ISO. I rapporti, i binari, i checksum completi dei media e gli artefatti di test restano fuori da Git.
Preservare QEMU, WinRE, SSH, TeamViewer, i montaggi NAS e i diagnostici. La remasterizzazione aggiunge soltanto il payload Codex e deve verificare che i file originali restino invariati.
