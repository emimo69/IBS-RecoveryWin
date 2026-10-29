# IBS – Codex AI: candidata separata 2.1

Questa copia nasce dal ramo `ibs-recoverywin-2.0`, commit
`c4cebb15b108f4952affba5cb0a2603cd2dc99b0`. La ISO esistente resta invariata.
Non sono modificati QEMU, WinRE, SSH, TeamViewer, Public o i diagnostici.
Il nuovo nome immagine e `IBS-RecoveryWin-2.1-Codex`.

## Utilizzo del tecnico

1. Doppio clic su **IBS – Codex AI** sul desktop.
2. Leggere il collegamento e il codice temporaneo; autenticarsi con il proprio
   account ChatGPT dal browser, anche su un altro dispositivo.
3. Attendere: al completamento si apre automaticamente Codex con
   `--no-alt-screen --yolo`. Non occorrono altri comandi Linux.
4. Usare `/quit` per terminare: il gestore esegue `codex logout` e rimuove i dati
   temporanei. Anche la chiusura normale della finestra viene gestita.

Nel terminale XFCE rimangono copia `Ctrl+Maiusc+C`, incolla `Ctrl+Maiusc+V`
e il menu destro. Non viene modificato il profilo del terminale o Clipman.
La modalita `--yolo`, richiesta dall'utente, permette a Codex di eseguire comandi
senza sandbox e senza approvazioni; i privilegi restano quelli dell'utente Live,
non viene avviato con sudo.

Il device login deve essere consentito nelle impostazioni dell'account/workspace.
Il collegamento non cambia impostazioni dell'account e non automatizza password,
MFA o l'approvazione personale nel browser. Un account senza accesso al servizio
puo autenticarsi ma non necessariamente inviare richieste: verificare il proprio piano.

## Autenticazione e separazione

Ogni avvio crea un nuovo `CODEX_HOME` casuale in un filesystem `tmpfs`, permessi
0700; il file di configurazione ha permessi 0600. La configurazione forza
`cli_auth_credentials_store="file"` e `forced_login_method="chatgpt"` anche
tramite argomenti CLI. Non viene usato il keyring di sistema.

Il gestore controlla `codex login status`, esegue `codex login --device-auth`
se necessario, attende la conclusione e ricontrolla lo stato prima della TUI.
Il primo controllo normalmente risulta non autenticato perche la directory
e nuova: un tecnico non eredita la sessione precedente.

Vengono eliminate dall'ambiente ereditato le variabili Codex/OpenAI dei provider;
nessuna API key o autenticazione del profilo abituale viene copiata.
Il lavoro del tecnico e in `~/IBS-Codex-Lavoro`, separato dall'autenticazione.
La cronologia persistente di Codex e disattivata. I restanti dati di sessione,
inclusi eventuali log di login generati da Codex, risiedono nella directory RAM
e vengono rimossi insieme ad essa. Non copiarli in progetti, rapporti o ISO.

La pulizia chiama logout, controlla che login status risulti disconnesso, quindi
rimuove soltanto la directory casuale creata dal gestore. Errori e timeout di
logout sono segnalati; la rimozione locale avviene comunque. Questo non implica
il logout del browser o di tutte le altre sessioni ChatGPT dell'account.

HUP e TERM vengono gestiti. Nessun programma puo eseguire logout dopo SIGKILL,
crash del kernel o perdita di alimentazione: l'autenticazione residua rimane
solo in RAM, non viene riutilizzata da un nuovo avvio e scompare al reboot.
Le directory private non costituiscono isolamento fra utenti ostili che
condividono lo stesso UID o privilegi root. I tecnici devono terminare la propria
sessione prima del passaggio della postazione.

## Distribuzione ripetibile senza credenziali

Codex CLI nativo amd64 musl 0.165.0 con il relativo `codex-code-mode-host`, release upstream fissata in
`assets/codex-release.json`. Nessun npm/Node o installer remoto eseguito.
`python3 scripts/prepare-codex.py` scarica l'archivio ufficiale, verifica dimensione
e SHA-256 fissati per entrambi gli archivi, estrae soltanto gli eseguibili attesi e li prepara nella copia
nuova in `config/includes.chroot/opt/ibs/codex/`.

Gli override CLI possono mostrare un avviso di esecuzione embedded senza server
condiviso in background. E compatibile con la sessione isolata: non viene avviato
un server Codex persistente condiviso fra tecnici. Un avviso di Code Mode host
mancante, invece, indica un pacchetto incompleto e deve essere corretto.

La preparazione non compila ISO, non incorpora configurazioni della Live e non
legge directory di autenticazione. Binario e cache sono ignorati da Git.
La licenza upstream e conservata in `licenses/codex/`; il hook installa anche
la licenza nella candidata. La release e fissata intenzionalmente: per aggiornarla
occorre verificare provenienza, digest e rifare il collaudo del login.

`0200-codex-ai.hook.chroot` verifica il binario preparato e blocca la build se
trova file di autenticazione Codex nelle directory della sorgente immagine.
All'apertura di XFCE una sola azione locale marca come attendibile soltanto il
collegamento identico a quello fornito dalla nuova immagine; non avvia Codex,
non usa rete e non installa un servizio persistente.

Il comando di build continua a richiedere autorizzazione esplicita. Prima di
un'eventuale unica build candidata vanno completati i test nella Live. Non e
necessario ricompilare per provare login e launcher.

### Candidata dalla ISO gia verificata

`python3 scripts/remaster-codex.py --authorized --base-iso /percorso/copia-base.iso`
utilizza `fakeroot`, `unsquashfs`, `mksquashfs` e `xorriso` gia installati. Non
richiede sudo e non cambia permessi, mount o servizi dell'host.

La ISO base viene aperta in lettura e confrontata prima/dopo in streaming.
Il manifest SHA-256 originale verifica la sorgente SquashFS. La copia del
filesystem conserva proprietari, modi e attributi estesi: ogni voce originale
viene confrontata prima/dopo l'aggiunta del solo payload Codex. Anche i permessi
e proprietari serializzati nel nuovo SquashFS sono confrontati con l'originale.
WinRE, TeamViewer e gli altri programmi non vengono ricompilati o reinstallati.

Il catalogo El Torito e l'area di avvio ibrida BIOS/UEFI vengono riprodotti da
`xorriso`; il manifest SHA-256 interno viene aggiornato. Output nuovo:
`IBS-RecoveryWin-2.1-Codex-amd64.hybrid.iso`, con checksum separato. Lo script
rifiuta di sovrascrivere una candidata o una directory root di lavoro gia
esistente. Un errore prima della scrittura ISO non implica una ISO compilata.

`scripts/test-codex-iso.py` prepara prove separate BIOS e UEFI con TCG, 1536 MB
RAM, CD virtuale in sola lettura, nessuna scheda di rete e nessun disco fisico.
Monitor QMP e variabili OVMF sono locali alla singola prova. La chiusura e
limitata al processo registrato dello specifico test. I test non abilitano KVM
o modificano la configurazione QEMU dei tecnici.

## Test

`python3 scripts/test-codex-ai.py` verifica con CLI simulata separazione fra
sessioni, argomenti, permessi, nessuna credenziale ereditata, Internet assente,
login fallito, stato post-login invalido, errore TUI, logout fallito e in timeout,
processo residuo, HUP e TERM su pseudoterminale. Questi test non dimostrano
un'autenticazione reale.

Il collaudo reale deve verificare: collegamento desktop, login device con un
account del tecnico, avvio TUI, risposta innocua senza strumenti, copia/incolla,
uscita/logout, directory autenticazione rimossa e un secondo avvio nuovamente
disconnesso. La futura ISO candidata richiede inoltre una prova dopo boot.
I rapporti effettivi restano fuori da Git; non dichiarare i test superati se non
eseguiti. Nessuna credenziale personale entra nella sorgente o nella ISO.

## Documentazione ufficiale

- [Autenticazione e CODEX_HOME](https://developers.openai.com/codex/auth)
- [Comandi CLI](https://developers.openai.com/codex/cli/reference)
- [Release fissata](https://github.com/openai/codex/releases/tag/rust-v0.165.0)
