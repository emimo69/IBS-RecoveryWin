"""No persistent authentication, no changes to existing recovery tools."""
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request


class SessionError(Exception):
    pass


class Interrupted(SessionError):
    pass


def isolated_environment(source, codex_home):
    # Do not inherit API credentials, alternate Codex homes, or provider overrides.
    env = {key: value for key, value in source.items()
           if not key.startswith(('CODEX_', 'OPENAI_', 'AZURE_OPENAI_'))}
    env['CODEX_HOME'] = str(codex_home)
    return env


def memory_root():
    for path in (Path('/run/user') / str(os.getuid()), Path('/dev/shm')):
        if not path.is_dir() or path.is_symlink() or not os.access(path, os.W_OK):
            continue
        result = subprocess.run(['findmnt', '-n', '-o', 'FSTYPE', '-T', str(path)],
                                capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip() == 'tmpfs':
            return path
    raise SessionError('Non trovo una directory temporanea in RAM. Nessun login eseguito.')


def internet_check():
    # HTTP errors still establish DNS/TLS connectivity. Login itself reports
    # account restrictions, service failures, proxies and device-auth errors.
    request = urllib.request.Request('https://auth.openai.com/', method='HEAD')
    try:
        with urllib.request.urlopen(request, timeout=10):
            pass
    except urllib.error.HTTPError as error:
        if error.code == 407:
            raise SessionError('Il proxy richiede autenticazione. Verificare la connessione Internet.') from error
    except (OSError, urllib.error.URLError) as error:
        raise SessionError('Connessione sicura a OpenAI non disponibile. Verificare Internet, data/ora e proxy. '
                           + str(error)) from error


class Session:
    def __init__(self, binary, parent, workspace, env=None, check=internet_check):
        self.binary = str(binary)
        self.parent = Path(parent)
        self.workspace = Path(workspace)
        self.source_env = os.environ if env is None else env
        self.check = check
        self.home = None
        self.child = None
        self.cleanup_errors = []

    def prepare(self):
        self.home = Path(tempfile.mkdtemp(prefix='ibs-codex-', dir=self.parent))
        self.env = isolated_environment(self.source_env, self.home)
        os.chmod(self.home, 0o700)
        self.workspace.mkdir(parents=True, exist_ok=True, mode=0o700)
        config = ('cli_auth_credentials_store = "file"\n'
                  'forced_login_method = "chatgpt"\n'
                  'check_for_update_on_startup = false\n'
                  '[history]\npersistence = "none"\n'
                  '[projects.' + json.dumps(str(self.workspace)) + ']\ntrust_level = "trusted"\n')
        config_path = self.home / 'config.toml'
        config_path.write_text(config, encoding='utf-8')
        os.chmod(config_path, 0o600)

    def args(self, *args):
        # Force file storage even if a project contains a .codex configuration.
        return [self.binary, '-c', 'cli_auth_credentials_store="file"',
                '-c', 'forced_login_method="chatgpt"', *args]

    def invoke(self, *args):
        self.child = subprocess.Popen(self.args(*args), cwd=self.workspace, env=self.env)
        try:
            return self.child.wait()
        finally:
            if self.child.poll() is not None:
                self.child = None

    def run(self):
        self.prepare()
        print('IBS – Codex AI\nAccount personale ChatGPT: autenticazione valida soltanto per questa sessione.', flush=True)
        if self.invoke('login', 'status') != 0:
            self.check()
            print('Autenticati dal browser usando il collegamento e il codice mostrati qui sotto.\n'
                  'Attendo il completamento; non occorrono altri comandi Linux.', flush=True)
            if self.invoke('login', '--device-auth') != 0:
                raise SessionError('Autenticazione non completata. Leggere il motivo sopra. '
                                   'Il login con codice deve essere consentito dal proprio account/workspace ChatGPT.')
            if self.invoke('login', 'status') != 0:
                raise SessionError('Codex non conferma il login. Sessione non avviata.')
        print('Avvio Codex. Copia: Ctrl+Maiusc+C; incolla: Ctrl+Maiusc+V oppure menu destro.\n'
              'Alla chiusura verranno eliminati i dati locali di autenticazione.', flush=True)
        result = self.invoke('--no-alt-screen', '--yolo')
        if result:
            raise SessionError('Codex si e chiuso con codice ' + str(result) + '. Leggere il motivo sopra.')

    def cleanup(self):
        if self.child and self.child.poll() is None:
            try:
                self.child.terminate()
                try:
                    self.child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.child.kill()
                    self.child.wait(timeout=5)
            except (OSError, subprocess.SubprocessError) as error:
                self.cleanup_errors.append('Errore arresto processo Codex: ' + str(error))
            self.child = None
        if self.home is None:
            return
        try:
            result = subprocess.run(self.args('logout'), cwd=self.workspace, env=self.env,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
            if result.returncode:
                self.cleanup_errors.append('Logout non confermato da Codex.')
            else:
                status = subprocess.run(self.args('login', 'status'), cwd=self.workspace, env=self.env,
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
                if status.returncode == 0 or (self.home / 'auth.json').exists():
                    self.cleanup_errors.append('Codex segnala ancora autenticazione dopo il logout.')
        except (OSError, subprocess.TimeoutExpired) as error:
            self.cleanup_errors.append('Errore durante logout: ' + str(error))
        finally:
            # This is ONLY the unique directory created by this Session, never a
            # caller-provided CODEX_HOME, user profile, workspace or mounted disk.
            if (self.home.parent != self.parent or not self.home.name.startswith('ibs-codex-')
                    or self.home.is_symlink()):
                self.cleanup_errors.append('Directory temporanea inattesa: rimozione rifiutata.')
            else:
                try:
                    shutil.rmtree(self.home)
                except OSError as error:
                    self.cleanup_errors.append('Impossibile rimuovere i dati temporanei: ' + str(error))


def pause_error(message):
    print('\nERRORE: ' + message, file=sys.stderr, flush=True)
    if sys.stdin.isatty():
        try:
            input('\nPremi Invio per chiudere questa finestra...')
        except (EOFError, KeyboardInterrupt, OSError):
            pass


def main():
    session = None
    error = None
    handlers = {}

    def interrupted(signum, frame):
        # Ctrl+C also reaches the foreground CLI: let its own UI handle it.
        if signum == signal.SIGINT and session and session.child:
            return
        raise Interrupted('Sessione interrotta (segnale ' + str(signum) + ').')

    try:
        if not sys.stdin.isatty():
            raise SessionError('Avvia IBS – Codex AI dal desktop in una finestra terminale.')
        binary = shutil.which('codex')
        if not binary:
            raise SessionError('Codex CLI non e installato in questa Live. Usare la nuova versione IBS-RecoveryWin.')
        if os.geteuid() == 0:
            raise SessionError('Avvia il collegamento come utente della Live, senza sudo.')
        workspace = Path.home() / 'IBS-Codex-Lavoro'
        if workspace.is_symlink():
            raise SessionError('La cartella IBS-Codex-Lavoro non deve essere un collegamento simbolico.')
        session = Session(binary, memory_root(), workspace)
        for sig in (signal.SIGHUP, signal.SIGTERM, signal.SIGINT):
            handlers[sig] = signal.signal(sig, interrupted)
        session.run()
    except (SessionError, OSError, subprocess.SubprocessError) as failure:
        error = str(failure)
    finally:
        # Terminal closure must not interrupt logout/temporary directory cleanup.
        for sig in handlers:
            signal.signal(sig, signal.SIG_IGN)
        if session:
            session.cleanup()
            if session.cleanup_errors:
                error = (error + '\n' if error else '') + '\n'.join(session.cleanup_errors)
        for sig, handler in handlers.items():
            signal.signal(sig, handler)
    if error:
        pause_error(error)
        return 1
    print('\nLogout completato. Dati temporanei della sessione rimossi.', flush=True)
    return 0
