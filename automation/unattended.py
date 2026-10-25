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

PROJECT = Path('/opt/ibs-recoverywin-1.0')
REMOTE = 'https://github.com/emimo69/IBS-RecoveryWin.git'
BRANCH = 'ibs-recoverywin-1.0'
SESSION_SECONDS = 7200


def busy():
    # Conservative: any Codex process blocks execution, including sandbox PID 1.
    # A PID namespace cannot certify host idleness, so never ignore PID 1.
    for proc in Path('/proc').glob('[0-9]*'):
        try:
            if 'codex' in (proc / 'comm').read_text().lower():
                return True
        except FileNotFoundError:
            pass
        except PermissionError:
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

    def execute(self, prompt):
        # Keep lock inherited by the process tree, even if the supervisor crashes.
        child = subprocess.Popen(['codex', '--ask-for-approval', 'never', 'exec',
                                  '--sandbox', 'workspace-write', '-C', str(self.project),
                                  '--json', prompt], stdout=subprocess.PIPE,
                                 stderr=subprocess.DEVNULL, start_new_session=True,
                                 pass_fds=(self.lock.fileno(),))
        import selectors
        selector = selectors.DefaultSelector()
        selector.register(child.stdout, selectors.EVENT_READ)
        os.set_blocking(child.stdout.fileno(), False)
        deadline = time.monotonic() + SESSION_SECONDS
        quota = False
        buffer = b''

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
                    buffer += chunk
                    while b'\n' in buffer:
                        line, buffer = buffer.split(b'\n', 1)
                        # Inspect errors only; never save message text or transcripts.
                        try:
                            event = json.loads(line)
                            if event.get('type') in ('error', 'turn.failed'):
                                value = json.dumps(event).lower()
                                quota |= any(x in value for x in (
                                    'rate_limit', 'rate limit', '429', 'quota', 'usage limit'))
                        except (ValueError, AttributeError):
                            pass
                    if len(buffer) > 1048576:
                        buffer = b''
            return child.wait(timeout=max(1, deadline-time.monotonic())), quota
        except (TimeoutError, subprocess.TimeoutExpired, InterruptedError):
            stop()
            return 124, False
        finally:
            selector.close()
            child.stdout.close()
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
            self.status(record['status'], task=blob, reason='hash_non_ripetibile')
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
                  'commit e push; se vietati o push fallisce fermati con diagnosi. '
                  'Non modificare CODEX-TASK.md. Riprendi eventuale lavoro incompleto già presente.')
        try:
            rc, quota = self.execute(prompt)
            if quota:
                record.update(status='quota_in_attesa', exit_code=rc,
                              next_attempt=int(time.time()) + 21600)
            else:
                remote = self.git('ls-remote', REMOTE, f'refs/heads/{BRANCH}').split()
                ok = (rc == 0 and self.verify() and self.clean() and remote and
                      remote[0] == self.git('rev-parse', 'HEAD') and
                      self.git('rev-parse', 'HEAD:CODEX-TASK.md') == blob)
                record.update(status='success' if ok else 'failed', exit_code=rc,
                              reason='verifica_git' if not ok else 'git_e_verify_config_verificati')
        except Exception:
            record.update(status='failed', exit_code=125, reason='verifica_o_avvio_fallito')
        self.write('runs/' + blob + '.json', record)
        self.status(record['status'], task=blob, exit_code=record['exit_code'])

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
