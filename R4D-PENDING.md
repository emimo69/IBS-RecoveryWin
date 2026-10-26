# R4D — PENDING

26 ottobre 2026, base 7f77574, repository inizialmente pulito.
Scrittura di docs/R4D-QEMU-VALIDATION.md negata dall'ambiente.
Directory docs: nobody:nogroup, modo 0775; nessuna modifica ai permessi tentata.
Rapporto e test non pubblicati: task incompleto, nessun commit/push tentato.

## Prova reale ripetibile

`PYTHONDONTWRITEBYTECODE=1 python3 scripts/test-qemu-ovmf-parser.py`

PASS: 1 test con 2 sottocasi, QEMU 10.0.13 Debian
1:10.0.13+ds-0+deb13u1. Nessun mock del parser.
Il test estrae esattamente le due opzioni -drive di vm.qemu_args.
Fixture CODE/VARS sparse raw da 4 MiB in directory temporanee del progetto.
Suffissi nei nomi: ` con spazi` e `,uno,,due con spazi,è`.
Una virgola viene codificata come due, due come quattro, dal codice esistente.
QMP query-block conferma i percorsi originali esatti, CODE ro=true,
VARS ro=false, esattamente due backend. SHA-256 di entrambi invariato.
QMP query-status conferma running=false; tutte le risposte senza errori,
uscita QEMU 0. Nessuna modifica al codice di produzione necessaria.

Argomenti QEMU di isolamento: -no-user-config -nodefaults -machine q35
-accel tcg -m 64 -S -display none -nic none -monitor none -serial none
-qmp stdio, seguiti dai due -drive di produzione.
QMP: qmp_capabilities, query-status, query-block, quit.
Timeout subprocess.run di 15 secondi con kill/reap automatico;
TemporaryDirectory rimuove le fixture anche in caso di errore.

## Regressioni reali eseguite, tutte con uscita 0

Script Python eseguiti con PYTHONDONTWRITEBYTECODE=1:

| Script in scripts/ | Risultato |
| --- | --- |
| test-vm.py | 9 PASS |
| test-media.py | 7 PASS |
| test-r4-paths.py | 3 PASS |
| test-remote.py | 8 PASS |
| test-launcher.py | 3 PASS |
| test-desktop-ip.py | 3 PASS |
| test-unattended.py | 13 PASS, offline |
| test-timer-diagnosis.py | 3 PASS, offline |
| test-qcow2-fixture.py | qemu-img/qemu-io: base RO invariata, overlay scrivibile e leggibile, check formati PASS |
| preflight-live.py | PASS statico |
| sh scripts/verify-config.sh | PASS, include verify-remote.py |

QCOW2: fixture conservate dal test preesistente in
.build/qcow2-fixture-oppvx6tt, escluse dalla pubblicazione.
git diff --check passato. Nessun fallimento dei test da correggere.

## Limiti

File firmware sintetici e CPU ferma: nessuna prova di boot OVMF o WinRE,
Windows, KVM, GUI, SSH o TeamViewer live. NAS/USB nei test sono mock.
Nessuna build, ISO avviata/cancellata, disco fisico, modifica servizi/timer,
altro progetto o utente. R2/R3/R4C e CODEX-TASK.md invariati.
test-live-qemu.py non eseguito: richiede boot ISO, fuori dal task.

## Piano futuro, solo previa autorizzazione

WinRE con ISO autorizzata RO, firmware OVMF reale CODE RO e copia VARS
temporanea, SOLO disco virtuale QCOW2 fittizio con overlay separato.
Verificare file regolari e disponibilità KVM prima del lancio, rete disabilitata,
timeout e cleanup garantito. Osservare boot/rilevamento del solo disco
virtuale e verificare hash base invariato. Nessun passthrough disco fisico.

## Ripresa

Risolvere esternamente il blocco di scrittura della directory docs senza
escalation da parte di Codex. Pubblicare il rapporto nella destinazione
richiesta, rieseguire i controlli opportuni, commit/push delle sole modifiche
validate e verifica dell'hash remoto. Fino ad allora stato PENDING.
La patch locale R4D-PENDING.patch conserva il test e questo rapporto.
