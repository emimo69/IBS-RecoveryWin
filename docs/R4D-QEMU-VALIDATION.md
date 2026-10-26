# R4D — Validazione parser QEMU

Rapporto finalizzato il 26 ottobre 2026 durante R5, base Git `8efbb16`,
ramo `ibs-recoverywin-1.0`, albero inizialmente pulito. Fonte delle prove
precedenti: `R4D-PENDING.md`, conservato insieme alla patch di riferimento;
la patch non è stata riapplicata. Nessuna modifica al codice di produzione.

## Prova reale rieseguita

`PYTHONDONTWRITEBYTECODE=1 python3 scripts/test-qemu-ovmf-parser.py`

Esito: 1 test con 2 sottocasi PASS, uscita 0, QEMU 10.0.13
(Debian `1:10.0.13+ds-0+deb13u1`). È il parser del processo QEMU reale,
senza mock, applicato esattamente alle due opzioni `-drive` prodotte da
`vm.qemu_args`. CODE e VARS sono fixture sparse raw da 4 MiB, non firmware
OVMF eseguibile, create in directory temporanee del progetto.

I suffissi verificati sono ` con spazi` e `,uno,,due con spazi,è`.
Il codice esistente raddoppia ciascuna virgola. `query-block` conferma i
percorsi originali esatti, due soli backend, CODE `ro=true`, VARS `ro=false`.
Gli SHA-256 di entrambi i file restano invariati. `query-status` conferma
`running=false`; tutte le risposte QMP hanno successo, uscita QEMU 0.

Isolamento: `-no-user-config -nodefaults -machine q35 -accel tcg -m 64
-S -display none -nic none -monitor none -serial none -qmp stdio`, poi
le due opzioni pflash di produzione. Sequenza QMP: `qmp_capabilities`,
`query-status`, `query-block`, `quit`. Il timeout di `subprocess.run` è
15 secondi e comporta kill/reap; `TemporaryDirectory` rimuove le fixture
anche in caso di errore.

## Regressioni rieseguite in R5

Tutti i Python con `PYTHONDONTWRITEBYTECODE=1`; tutte le uscite sono 0.

| Comando | Esito |
| --- | --- |
| `python3 scripts/test-vm.py` | 9 PASS |
| `python3 scripts/test-media.py` | 7 PASS |
| `python3 scripts/test-r4-paths.py` | 3 PASS |
| `sh scripts/verify-config.sh` | PASS statico, include `verify-remote.py` e sintassi shell |

I test media/percorsi NAS e Ventoy usano mock: non attestano dispositivi,
mount o servizi reali. La verifica configurazione non è una build né una
verifica live di TeamViewer, SSH o IP.

## Evidenze precedenti, non rieseguite in R5

`R4D-PENDING.md` registra uscite 0 per: remote (8), launcher (3), desktop IP
(3), unattended (13 offline), timer diagnosis (3 offline), preflight live
statico e `git diff --check`. Registra inoltre `test-qcow2-fixture.py` con
qemu-img/qemu-io: base RO invariata, overlay scrivibile e leggibile,
controlli formato PASS. Quelle fixture sono conservate in
`.build/qcow2-fixture-oppvx6tt`, escluse dalla pubblicazione.
Questi risultati sono storici, non nuove prove effettuate da R5.

## Conclusione e limiti

Verificati il parsing pflash dei percorsi problematici e i flag RO/RW
con QEMU reale, senza eseguire CPU guest. **Boot OVMF e WinRE non verificati**.
Non verificati Windows, KVM, GUI, SSH/TeamViewer live, NAS o USB reali.
`test-live-qemu.py` non eseguito perché richiede boot ISO.

Nessuna build, nessun avvio ISO, accesso a dischi fisici, modifica a servizi,
timer, credenziali o altri progetti. ISO R2/R3 non aperte né modificate.
Il prossimo collaudo resta subordinato alle condizioni del piano
[R5-WINRE-TEST-PLAN.md](../R5-WINRE-TEST-PLAN.md).
