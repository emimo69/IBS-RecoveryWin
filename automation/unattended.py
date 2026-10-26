#!/usr/bin/env python3
"""Noninteractive runner. No transcript or Git diagnostics are persisted."""
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def classify_error(message):
    value = message.lower()
    if any(x in value for x in ('rate_limit', 'rate limit', '429', 'quota', 'usage limit')):
        return 'quota'
    if any(x in value for x in ('permission denied', 'operation not permitted', 'read-only file system', 'sandbox', 'bubblewrap', 'bwrap:')):
        return 'sandbox_permessi'
    if any(x in value for x in ('not logged in', 'unauthorized', 'authentication', 'login required', 'invalid token')):
        return 'autenticazione'
    if any(x in value for x in ('dns', 'network unreachable', 'connection refused', 'connection timed out', 'connection error')):
        return 'rete'
    return 'non_classificato'

PROJECT = Path('/opt/ibs-recoverywin-1.0')
REMOTE = 'https://github.com/emimo69/IBS-RecoveryWin.git'
BRANCH = 'ibs-recoverywin-1.0'
SESSION_SECONDS = 7200


def busy():
    """True for interactive/exec Codex sessions or when process visibility is insufficient.

    Long-lived Codex app-server and code-mode-host helper daemons are not jobs.
    Only ignore these two recognizable helper executable names, never arbitrary
    commands containing those strings in their arguments.
    """
    for proc in Path('/proc').glob('[0-9]*'):
        try:
            raw = (proc / 'cmdline').read_bytes()
            args = [x.decode('utf-8', 'replace') for x in raw.split(bytes([0])) if x]
            if not args:
                continue
            executable = Path(args[0]).name.lower()
            if executable in ('codex-code-mode-host',):
                continue
            if executable == 'codex' and len(args) > 1 and args[1] == 'app-server':
                continue
            if executable == 'codex' or executable.startswith('codex-'):
                return True
        except FileNotFoundError:
            continue
        except (PermissionError, OSError):
            return True
    return False


class Runner:
    def __init__(self, project=PROJECT):
        self.project = project
        self.state = project / '.task-watch'
        self.state.mkdir(exist_ok=True, mode=0o700)
        self.monitor = self.state / 'monitor.git'

    def write(self, name, data):
        path = self.state / name
        path.parent.mkdir(exist_ok=True, mode=0o700)
        tmp = path.with_suffix('.tmp')
        tmp.write_text(json.dumps(data, sort_keys=True) + '\n')
        tmp.replace(path)

    def status(self, message, **fields):
        self.write('runner-status.json', dict(timestamp=int(time.time()), status=message, **fields))

    def git(self, *args, monitor=False):
        where = ['--git-dir', str(self.monitor)] if monitor else ['-C', str(self.project)]
        return subprocess.run(['git', *where, *args], check=True, stdout=subprocess.PIPE,
                              stderr=subprocess.DEVNULL, text=True, timeout=60,
                              env=dict(os.environ, GIT_TERMINAL_PROMPT='0')).stdout.strip()

    def fetch(self):
        if not self.monitor.exists():
            subprocess.run(['git', 'init', '--bare', str(self.monitor)], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
        self.git('fetch', '--quiet', '--no-tags', REMOTE,
                 f'+refs/heads/{BRANCH}:refs/heads/monitor', monitor=True)
        commit = self.git('rev-parse', 'refs/heads/monitor', monitor=True)
        blob = self.git('rev-parse', f'{commit}:CODEX-TASK.md', monitor=True)
        if self.git('cat-file', '-t', blob, monitor=True) != 'blob':
            raise RuntimeError('invalid_task')
        return commit, blob

    def clean(self):
        return not self.git('status', '--porcelain', '--untracked-files=all')

    def verify(self):
        return subprocess.run(['bash', str(self.project / 'scripts/verify-config.sh')],
                              cwd=self.project, stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL, timeout=120).returncode == 0

    def publish_verified(self, task_blob):
        """Host-side publisher: allow only additive/modified non-sensitive source and tests.

        Codex's workspace sandbox cannot write .git or use GitHub network. The
        service's ordinary user account performs checked staging and publication.
        """
        import re
        changed = self.git('status', '--porcelain', '--untracked-files=all').splitlines()
        if not changed:
            raise RuntimeError('nessuna_modifica_prodotta')
        paths = []
        for line in changed:
            if len(line) < 4 or line[:2] not in (' M', 'M ', 'MM', '??'):
                raise RuntimeError('modifica_non_autorizzata')
            path = line[3:]
            if not re.fullmatch(r'(?:scripts/test-[a-zA-Z0-9_-]+\.py|docs/[a-zA-Z0-9_./-]+\.md|R[0-9][A-Z]?-PROGRESS\.md|config/includes\.chroot/usr/local/lib/ibs-recovery/[a-zA-Z0-9_-]+\.py)', path):
                raise RuntimeError('percorso_non_autorizzato')
            target = self.project / path
            if target.is_symlink() or not target.is_file() or target.stat().st_size > 150000:
                raise RuntimeError('file_non_sicuro')
            paths.append(path)
        if self.git('rev-parse', 'HEAD:CODEX-TASK.md') != task_blob:
            raise RuntimeError('task_modificato')
        # Confirm remote has not advanced since this worker fetched the task.
        before = self.git('rev-parse', 'HEAD')
        remote = self.git('ls-remote', REMOTE, f'refs/heads/{BRANCH}').split()
        if not remote or remote[0] != before:
            raise RuntimeError('remote_divergente')
        # Do not stage or upload credentials, executables, generated binaries or patches.
        self.git('add', '--', *paths)
        self.git('diff', '--cached', '--check')
        # All static and software tests must pass BEFORE a commit is created.
        for cmd in (['python3','-B','scripts/test-vm.py'],
                    ['python3','-B','scripts/test-media.py'],
                    ['bash','scripts/verify-config.sh']):
            subprocess.run(cmd,cwd=self.project,check=True,stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL,timeout=120)
        self.git('commit', '-m', 'Codex: modifiche verificate automaticamente')
        self.git('push', 'origin', f'HEAD:{BRANCH}')
        published = self.git('ls-remote', REMOTE, f'refs/heads/{BRANCH}').split()
        if not published or published[0] != self.git('rev-parse', 'HEAD'):
            raise RuntimeError('push_non_confermato')
        return 'pubblicato'

    def execute(self, prompt):
        # Keep lock inherited by the process tree, even if the supervisor crashes.
        child = subprocess.Popen(['codex', '--ask-for-approval', 'never', 'exec',
                                  '--sandbox', 'workspace-write', '-C', str(self.project),
                                  '--json', prompt], stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, start_new_session=True,
                                 pass_fds=(self.lock.fileno(),))
        import selectors
        selector = selectors.DefaultSelector()
        selector.register(child.stdout, selectors.EVENT_READ)
        selector.register(child.stderr, selectors.EVENT_READ)
        os.set_blocking(child.stdout.fileno(), False)
        deadline = time.monotonic() + SESSION_SECONDS
        quota = False
        buffers = {child.stdout.fileno(): b'', child.stderr.fileno(): b''}
        cause = 'non_classificato'

        def stop(signum=None, frame=None):
            try:
                os.killpg(child.pid, signal.SIGTERM)
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
            except ProcessLookupError:
                pass

        previous = {s: signal.signal(s, lambda a, b: (_ for _ in ()).throw(InterruptedError()))
                    for s in (signal.SIGTERM, signal.SIGINT)}
        try:
            while selector.get_map():
                if time.monotonic() >= deadline:
                    raise TimeoutError()
                for key, _ in selector.select(timeout=1):
                    chunk = os.read(key.fd, 65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    data = buffers.get(key.fd, b'') + chunk
                    while b'\n' in data:
                        line, data = data.split(b'\n', 1)
                        # Classify only: never save raw errors, model output or secrets.
                        category = classify_error(line.decode('utf-8', 'replace'))
                        if category != 'non_classificato':
                            cause = category
                            quota |= category == 'quota'
                    buffers[key.fd] = data[-4096:]
            # A final stderr/stdout fragment may have no terminating newline.
            # Classify it too, without persisting the underlying output.
            for tail in buffers.values():
                if tail:
                    category = classify_error(tail.decode('utf-8', 'replace'))
                    if category != 'non_classificato':
                        cause = category
                        quota |= category == 'quota'
            self.last_cause = cause
            return child.wait(timeout=max(1, deadline-time.monotonic())), quota
        except (TimeoutError, subprocess.TimeoutExpired, InterruptedError):
            stop()
            self.last_cause = 'timeout_o_interruzione'
            return 124, False
        finally:
            selector.close()
            child.stdout.close()
            child.stderr.close()
            for sig, handler in previous.items():
                signal.signal(sig, handler)

    def tick(self, mode):
        commit, blob = self.fetch()
        waiting = sorted((self.state / 'runs').glob('*.json'))
        for path in waiting:
            saved = json.loads(path.read_text())
            if saved.get('status') == 'quota_in_attesa':
                commit, blob = saved['commit'], saved['task']
                break
        self.status('rilevato', commit=commit, task=blob)
        marker = self.state / 'runs' / (blob + '.json')
        record = json.loads(marker.read_text()) if marker.exists() else {}
        if (self.state / 'completed' / blob).exists():
            self.status('success', task=blob)
            return
        if record.get('status') == 'running':
            record.update(status='failed', exit_code=125, reason='sessione_interrotta')
            self.write('runs/' + blob + '.json', record)
        if record and record.get('status') != 'quota_in_attesa':
            self.status(record['status'], task=blob, exit_code=record.get('exit_code'),
                        reason=record.get('reason', 'hash_non_ripetibile'))
            return
        if record.get('next_attempt', 0) > time.time():
            self.status('quota_in_attesa', task=blob, next_attempt=record['next_attempt'])
            return
        if mode != 'unattended' or not (self.state / 'unattended-enabled').exists():
            self.status('poll', task=blob)
            return
        if busy():
            self.status('poll_codex_attivo', task=blob)
            return
        if (self.state / 'blocked').exists():
            self.status('bloccato', task=blob)
            return
        if self.git('branch', '--show-current') != BRANCH or (not record and not self.clean()):
            self.status('bloccato_worktree', task=blob)
            return
        if self.git('remote', 'get-url', 'origin') != REMOTE:
            raise RuntimeError('origin_inatteso')
        # Resume quota work only at the original pinned task; never replace it.
        if record and self.git('rev-parse', 'HEAD:CODEX-TASK.md') != blob:
            self.status('bloccato_task_quota', task=blob)
            return
        if not record:
            self.git('fetch', '--no-tags', str(self.monitor), commit)
            self.git('merge', '--ff-only', commit)
        if self.git('rev-parse', 'HEAD:CODEX-TASK.md') != blob or busy():
            self.status('poll_verifica_task', task=blob)
            return
        record = dict(status='running', task=blob, commit=record.get('commit', commit),
                      started=int(time.time()), exit_code=None)
        self.write('runs/' + blob + '.json', record)
        self.status('running', task=blob)
        prompt = ('Leggi AGENTS.md e CODEX-TASK.md. Esegui solo il task software nel progetto '
                  '/opt/ibs-recoverywin-1.0. Non modificare altri progetti o utenti, dischi fisici, '
                  'non riavviare host, non cancellare ISO. Build solo se autorizzata dal task. '
                  'Nessuna escalation o aggiramento sandbox. Non leggere o pubblicare credenziali. '
                  'Correggi i fallimenti dei test consentiti e rieseguili. Esegui verifiche reali, '
                  'NON eseguire commit o push: il runner pubblica dopo le verifiche. '
                  'Non modificare CODEX-TASK.md. Riprendi eventuale lavoro incompleto già presente.')
        try:
            rc, quota = self.execute(prompt)
            if quota:
                record.update(status='quota_in_attesa', exit_code=rc,
                              next_attempt=int(time.time()) + 21600)
            else:
                if rc == 0:
                    publication = self.publish_verified(blob)
                    remote = self.git('ls-remote', REMOTE, f'refs/heads/{BRANCH}').split()
                    ok = (self.verify() and self.clean() and remote and
                          remote[0] == self.git('rev-parse', 'HEAD') and
                          self.git('rev-parse', 'HEAD:CODEX-TASK.md') == blob)
                else:
                    publication, ok = 'nessuna', False
                record.update(status='success' if ok else 'failed', exit_code=rc,
                              reason=('codex_' + getattr(self, 'last_cause', 'non_classificato') if rc != 0
                                      else publication if ok else 'verifica_git'))
        except Exception as exc:
            category = str(exc) if str(exc) in ('nessuna_modifica_prodotta','modifica_non_autorizzata','percorso_non_autorizzato','file_non_sicuro','task_modificato','remote_divergente','push_non_confermato') else 'verifica_o_avvio_fallito'
            record.update(status='failed', exit_code=125, reason=category)
        self.write('runs/' + blob + '.json', record)
        self.status(record['status'], task=blob, exit_code=record['exit_code'],
                    reason=record.get('reason', 'nessuna'))

    def run(self, mode):
        self.lock = (self.state / 'lock').open('a')
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.lock.close()
            return
        try:
            self.tick(mode)
        except Exception:
            self.status('errore_controllo', reason='git_rete_o_stato_non_disponibile')
        finally:
            self.lock.close()


if __name__ == '__main__':
    os.umask(0o077)
    if os.getuid() == 0:
        sys.exit('Non eseguire come root')
    mode = sys.argv[1] if len(sys.argv) == 2 else 'poll'
    if mode not in ('poll', 'unattended'):
        sys.exit(2)
    Runner().run(mode)
