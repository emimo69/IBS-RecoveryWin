#!/usr/bin/env python3
"""Launcher robustness tests; fake CLI never authenticates a real account."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import signal
import time
import tempfile
import unittest
from unittest import mock
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('session', ROOT / 'config/includes.chroot/usr/local/lib/ibs-codex/session.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

FAKE = '''#!/usr/bin/python3
import json,os,sys,time
from pathlib import Path
a=sys.argv[1:]
with open(os.environ['IBS_TEST_CALLS'],'a') as f:
 f.write(json.dumps({'args':a,'home':os.environ['CODEX_HOME'],'pid':os.getpid(),'api_inherited':any(k.startswith(('OPENAI_','AZURE_OPENAI_')) for k in os.environ)})+'\\n')
while a and a[0]=='-c':a=a[2:]
p=Path(os.environ['CODEX_HOME'])/'auth.json'
mode=os.environ.get('IBS_TEST_FAILURE','')
if a==['login','status']:
 sys.exit(0 if p.exists() else 1)
if a==['login','--device-auth']:
 if mode=='login':sys.exit(7)
 if mode!='status':p.write_text('{"fake_test_account":true}')
 sys.exit(0)
if a==['logout']:
 if mode=='logout':sys.exit(8)
 if p.exists():p.unlink()
 sys.exit(0)
if a==['--no-alt-screen','--yolo']:
 if mode=='wait':time.sleep(60)
 sys.exit(9 if mode=='tui' else 0)
sys.exit(23)
'''


class PureTests(unittest.TestCase):
    def test_environment_replaces_home_and_removes_provider_credentials(self):
        source={'CODEX_HOME':'old','CODEX_API_KEY':'fake','CODEX_ACCESS_TOKEN':'fake',
                'OPENAI_API_KEY':'fake','OPENAI_BASE_URL':'old','AZURE_OPENAI_API_KEY':'fake',
                'DISPLAY':':0','HTTP_PROXY':'proxy','HOME':'profile'}
        env=MODULE.isolated_environment(source,Path('/new'))
        self.assertEqual(env,{'DISPLAY':':0','HTTP_PROXY':'proxy','HOME':'profile','CODEX_HOME':'/new'})
        self.assertEqual(source['CODEX_HOME'],'old')

    def test_network_failure_is_comprehensible(self):
        with mock.patch.object(MODULE.urllib.request,'urlopen',side_effect=urllib.error.URLError('offline')):
            with self.assertRaisesRegex(MODULE.SessionError,'Internet'):
                MODULE.internet_check()

    def test_http_forbidden_is_not_mistaken_for_no_internet(self):
        error=urllib.error.HTTPError('https://auth.openai.com',403,'Forbidden',{},None)
        with mock.patch.object(MODULE.urllib.request,'urlopen',side_effect=error):
            MODULE.internet_check()

    def test_proxy_auth_error(self):
        error=urllib.error.HTTPError('https://auth.openai.com',407,'Proxy',{},None)
        with mock.patch.object(MODULE.urllib.request,'urlopen',side_effect=error):
            with self.assertRaisesRegex(MODULE.SessionError,'proxy'):
                MODULE.internet_check()

    def test_error_keeps_terminal_open(self):
        with mock.patch.object(MODULE.sys.stdin,'isatty',return_value=True), mock.patch('builtins.input') as read:
            MODULE.pause_error('errore simulato')
            read.assert_called_once()

    def test_already_closed_terminal_does_not_break_cleanup(self):
        with mock.patch.object(MODULE.sys.stdin,'isatty',return_value=True), mock.patch('builtins.input',side_effect=OSError('closed tty')):
            MODULE.pause_error('terminale chiuso')

    def test_memory_root_refuses_persistent_storage(self):
        result=subprocess.CompletedProcess([],0,'ext4\n','')
        with mock.patch.object(MODULE.subprocess,'run',return_value=result):
            with self.assertRaisesRegex(MODULE.SessionError,'RAM'):
                MODULE.memory_root()


@unittest.skipUnless(os.name=='posix','Native subprocess tests require the Linux Live')
class LinuxTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='ibs-codex-test-')
        self.root=Path(self.temp.name)
        self.binary=self.root/'codex'
        self.binary.write_text(FAKE)
        self.binary.chmod(0o755)
        self.workspace=self.root/'workspace'
        self.calls=self.root/'calls.jsonl'
        self.env=dict(os.environ,IBS_TEST_CALLS=str(self.calls),OPENAI_API_KEY='fake-not-a-real-key')

    def tearDown(self):
        self.temp.cleanup()

    def session(self, failure='', check=lambda:None):
        env=dict(self.env,IBS_TEST_FAILURE=failure)
        return MODULE.Session(self.binary,self.root,self.workspace,env,check)

    def records(self):
        return [json.loads(s) for s in self.calls.read_text().splitlines()]

    def execute(self,session):
        try:session.run()
        finally:session.cleanup()

    def test_full_lifecycle_and_exact_flags(self):
        session=self.session()
        self.execute(session)
        records=self.records()
        self.assertEqual([r['args'][4:] for r in records],[['login','status'],['login','--device-auth'],
            ['login','status'],['--no-alt-screen','--yolo'],['logout'],['login','status']])
        self.assertFalse(session.home.exists())
        self.assertFalse(session.cleanup_errors)
        self.assertTrue(all(not r['api_inherited'] for r in records))
        self.assertEqual(len(set(r['home'] for r in records)),1)

    def test_next_technician_gets_new_home_and_login(self):
        first=self.session();self.execute(first)
        second=self.session();self.execute(second)
        self.assertNotEqual(first.home,second.home)
        self.assertEqual(sum(r['args'][4:]==['login','--device-auth'] for r in self.records()),2)

    def test_private_home_and_file_permissions(self):
        session=self.session();session.prepare()
        try:
            self.assertEqual(session.home.stat().st_mode & 0o777,0o700)
            self.assertEqual((session.home/'config.toml').stat().st_mode & 0o777,0o600)
            self.assertIn('cli_auth_credentials_store = "file"',(session.home/'config.toml').read_text())
        finally:session.cleanup()

    def test_existing_project_files_are_preserved(self):
        self.workspace.mkdir();marker=self.workspace/'project.txt';marker.write_text('keep')
        profile=self.root/'old-profile';profile.mkdir();(profile/'auth.json').write_text('not-an-account')
        self.env['CODEX_HOME']=str(profile)
        self.execute(self.session())
        self.assertEqual(marker.read_text(),'keep')
        self.assertEqual((profile/'auth.json').read_text(),'not-an-account')

    def test_failed_login_never_starts_tui_and_cleans(self):
        session=self.session('login')
        with self.assertRaisesRegex(MODULE.SessionError,'Autenticazione'):
            self.execute(session)
        self.assertFalse(session.home.exists())
        self.assertFalse(any('--yolo' in r['args'] for r in self.records()))

    def test_invalid_post_login_status_prevents_tui(self):
        session=self.session('status')
        with self.assertRaisesRegex(MODULE.SessionError,'non conferma'):
            self.execute(session)
        self.assertFalse(any('--yolo' in r['args'] for r in self.records()))

    def test_no_internet_does_not_start_login(self):
        def offline():raise MODULE.SessionError('Internet offline')
        session=self.session(check=offline)
        with self.assertRaisesRegex(MODULE.SessionError,'Internet'):
            self.execute(session)
        self.assertEqual([r['args'][4:] for r in self.records()],[['login','status'],['logout'],['login','status']])

    def test_tui_failure_still_logs_out(self):
        session=self.session('tui')
        with self.assertRaisesRegex(MODULE.SessionError,'codice 9'):
            self.execute(session)
        self.assertFalse(session.home.exists())
        self.assertIn(['logout'],[r['args'][4:] for r in self.records()])

    def test_failed_logout_still_removes_auth_home_and_reports(self):
        session=self.session('logout');self.execute(session)
        self.assertFalse(session.home.exists())
        self.assertTrue(session.cleanup_errors)

    def test_logout_timeout_still_removes_auth(self):
        session=self.session();session.prepare();(session.home/'auth.json').write_text('fake')
        with mock.patch.object(MODULE.subprocess,'run',side_effect=subprocess.TimeoutExpired('codex logout',15)):
            session.cleanup()
        self.assertFalse(session.home.exists())
        self.assertTrue(session.cleanup_errors)

    def test_unfinished_child_is_stopped_before_cleanup(self):
        session=self.session();session.prepare()
        child=subprocess.Popen(['/bin/sleep','60']);session.child=child
        session.cleanup()
        self.assertIsNotNone(child.poll())
        self.assertFalse(session.home.exists())

    def interrupted_terminal(self, sig):
        import pty
        master, slave=pty.openpty()
        env=dict(self.env,HOME=str(self.root),PATH=str(self.root)+':/usr/bin:/bin',IBS_TEST_FAILURE='wait')
        runner=self.root/'runner.py'
        runner.write_text('import importlib.util\ns=importlib.util.spec_from_file_location("session",'+repr(str(SPEC.origin))+')\nm=importlib.util.module_from_spec(s);s.loader.exec_module(m)\nraise SystemExit(m.main())\n')
        proc=subprocess.Popen(['/usr/bin/python3',str(runner)],env=env,stdin=slave,stdout=slave,stderr=slave,start_new_session=True)
        os.close(slave)
        try:
            deadline=time.monotonic()+8
            while time.monotonic()<deadline:
                if self.calls.exists() and any('--yolo' in r['args'] for r in self.records()):
                    break
                time.sleep(.05)
            else:self.fail('TUI fake did not start')
            records=self.records();home=Path(records[-1]['home']);child_pid=records[-1]['pid']
            os.kill(proc.pid,sig)
            os.write(master,b'\n')
            proc.wait(timeout=8)
            self.assertFalse(home.exists())
            self.assertIn(['logout'],[r['args'][4:] for r in self.records()])
            with self.assertRaises(ProcessLookupError):os.kill(child_pid,0)
        finally:
            if proc.poll() is None:proc.kill();proc.wait()
            os.close(master)

    def test_terminal_hangup_logs_out_and_removes_auth(self):
        self.interrupted_terminal(signal.SIGHUP)

    def test_termination_logs_out_and_removes_auth(self):
        self.interrupted_terminal(signal.SIGTERM)


if __name__=='__main__':
    unittest.main(verbosity=2)
