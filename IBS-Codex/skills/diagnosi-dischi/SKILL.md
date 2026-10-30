# Diagnosi dischi Windows
1. Rilevare disco Live e dischi cliente, identificando modello, seriale abbreviato, dimensione, RO/RW e punto di montaggio.
2. Acquisire `lsblk`, `blkid -p`, `smartctl -a` oppure `nvme smart-log`, `sfdisk --dump` soltanto se in lettura. Non montare automaticamente.
3. Per NTFS/GPT distinguere problemi SMART, controller/VMD, tabella partizioni, filesystem e BitLocker. Non eseguire `ntfsfix`, `fsck` in riparazione, `chkdsk /f`, `diskpart clean`.
4. Report: evidenza → impatto → ipotesi → eventuale azione proposta. Attendere autorizzazione.
