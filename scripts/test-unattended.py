#!/usr/bin/env python3
"""Offline behavior tests. No real Codex, Git network or systemd."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import json
import fcntl

spec = importlib.util.spec_from_file_location('runner', Path(__file__).resolve().parents[1] / 'automation/unattended.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class Tests(unittest.TestCase):
    def setUp(self):
        (m.PROJECT / '.task-watch').mkdir(exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir='/opt/ibs-recoverywin-1.0/.task-watch')
        self.addCleanup(self.tmp.cleanup)
        self.r = m.Runner(Path(self.tmp.name))
        self.r.fetch = lambda: ('a'*40, 'b'*40)
        self.r.execute = __import__('unittest.mock', fromlist=['Mock']).Mock(return_value=(0, False))
        self.r.git = self.git
        self.r.verify = lambda: True
        self.r.publish_verified = lambda blob: 'pubblicato'
        (self.r.state / 'unattended-enabled').touch()
        self.busy = patch.object(m, 'busy', return_value=False)
        self.busy.start()
        self.addCleanup(self.busy.stop)
        self.dirty = False
        self.remote = 'c'*40
    def git(self, *args, **kw):
        if args[0] == 'branch': return m.BRANCH
        if args[0] == 'status': return ' M file' if self.dirty else ''
        if args[0] == 'remote': return m.REMOTE
        if args[0] == 'ls-remote': return self.remote + '\trefs/heads/' + m.BRANCH
        if args[0] == 'rev-parse': return 'b'*40 if ':' in args[1] else 'c'*40
        return ''
    def marker(self):
        return json.loads((self.r.state / 'runs' / ('b'*40 + '.json')).read_text())
    def tick(self): self.r.run('unattended')
    def test_no_deliverable_is_failure(self):
        self.r.publish_verified = lambda blob: (_ for _ in ()).throw(RuntimeError('nessuna_modifica_prodotta'))
        self.tick()
        self.assertEqual(self.marker()['status'], 'failed')
        self.assertEqual(self.marker()['reason'], 'nessuna_modifica_prodotta')

    def test_success_dedup(self):
        self.tick(); self.tick()
        self.assertEqual(self.marker()['status'], 'success')
        self.r.execute.assert_called_once()
    def test_dirty(self):
        self.dirty = True; self.tick(); self.r.execute.assert_not_called()
    def test_busy(self):
        with patch.object(m, 'busy', return_value=True): self.tick()
        self.r.execute.assert_not_called()
    def test_poll(self):
        self.r.run('poll'); self.r.execute.assert_not_called()
    def test_disabled(self):
        (self.r.state / 'unattended-enabled').unlink()
        self.tick(); self.r.execute.assert_not_called()
    def test_failed_not_retried(self):
        self.r.execute.return_value = (1, False)
        self.tick(); self.tick()
        self.assertEqual(self.marker()['status'], 'failed')
        self.r.execute.assert_called_once()
    def test_exit_zero_remote_mismatch(self):
        self.remote = 'd'*40; self.tick()
        self.assertEqual(self.marker()['status'], 'failed')
    def test_restart(self):
        self.r.write('runs/'+'b'*40+'.json', dict(status='running', commit='a'*40, task='b'*40))
        self.tick(); self.r.execute.assert_not_called()
        self.assertEqual(self.marker()['exit_code'], 125)
    def test_quota_backoff_and_pinned_resume(self):
        self.r.execute.return_value = (1, True)
        self.tick(); self.tick()
        self.r.execute.assert_called_once()
        record = self.marker(); record['next_attempt'] = 0
        self.r.write('runs/'+'b'*40+'.json', record)
        self.r.fetch = lambda: ('e'*40, 'f'*40)
        self.r.execute.return_value = (0, False)
        self.dirty = True
        self.tick()
        self.assertEqual(self.r.execute.call_count, 2)
        self.assertEqual(self.marker()['task'], 'b'*40)
    def test_timeout_not_retried(self):
        self.r.execute.return_value = (124, False)
        self.tick(); self.tick(); self.r.execute.assert_called_once()
    def test_lock(self):
        with (self.r.state / 'lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.tick()
        self.r.execute.assert_not_called()

    def test_verification_failure(self):
        self.r.verify = lambda: False
        self.tick()
        self.assertEqual(self.marker()['status'], 'failed')
    def test_error_without_trailing_newline(self):
        import subprocess
        original = subprocess.Popen
        def fake_codex(*args, **kwargs):
            return original(['python3', '-c',
                             "import sys; sys.stderr.write('Read-only file system'); sys.exit(1)"],
                            **kwargs)
        self.r.lock = (self.r.state / 'lock').open('a')
        try:
            with patch.object(m.subprocess, 'Popen', side_effect=fake_codex):
                rc, quota = m.Runner.execute(self.r, 'mock')
            self.assertEqual(rc, 1)
            self.assertFalse(quota)
            self.assertEqual(self.r.last_cause, 'sandbox_permessi')
        finally:
            self.r.lock.close()

    def test_real_child_termination(self):
        import subprocess
        original = subprocess.Popen
        def fake_codex(*args, **kwargs):
            return original(['python3', '-c', 'import time; time.sleep(30)'], **kwargs)
        self.r.lock = (self.r.state / 'lock').open('a')
        try:
            with patch.object(m.subprocess, 'Popen', side_effect=fake_codex), patch.object(m, 'SESSION_SECONDS', 0.02):
                rc, quota = m.Runner.execute(self.r, 'mock')
            self.assertEqual(rc, 124)
            self.assertFalse(quota)
        finally:
            self.r.lock.close()

unittest.main()
