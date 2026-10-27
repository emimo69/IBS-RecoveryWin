#!/usr/bin/env python3
"""Execute a path-relocated copy with fake CLI tools; no daemon or /mnt writes."""
from pathlib import Path
import os
import configparser
import subprocess
import tempfile
import unittest

PROJECT = Path('/opt/ibs-recoverywin-2.0')
SOURCE = PROJECT / 'config/includes.chroot/usr/local/sbin/ibs-remote'

class RemoteTests(unittest.TestCase):
    def run_case(self, *, info='TeamViewer ID: 123456789', info_rc=0,
                 password_rc=0, password_output="ok", openssl_rc=0, ip=True, success=False, eula=True, info_after=0, desktop=True):
        with tempfile.TemporaryDirectory(prefix='.remote-test-', dir=PROJECT) as tmp:
            root = Path(tmp)
            bindir = root / 'bin'
            bindir.mkdir()
            conf = root / 'tvconf'
            conf.mkdir(parents=True)
            (conf / 'global.conf').write_text('[int32] EulaAccepted = ' + ('1' if eula else '0') + '\n')
            source = SOURCE.read_text().replace('/mnt', str(root / 'output')).replace('/etc/teamviewer', str(conf))
            source = source.replace('/proc/$XPID/environ', str(root / 'session-environ')).replace('/run/ibs-teamviewer-gui.log', str(root / 'gui.log'))
            (root / 'session-environ').write_bytes(b'DISPLAY=:99\0XAUTHORITY=/test/auth\0DBUS_SESSION_BUS_ADDRESS=unix:path=/test/bus\0XDG_RUNTIME_DIR=/run/user/1000\0')
            self.assertNotIn('/mnt/teamviewer.txt', source)
            self.assertNotIn('/etc/teamviewer', source)
            script = root / 'remote'
            script.write_text(source)
            commands = {
                'teamviewer': '''case "$1" in
license) printf '[int32] EulaAccepted = 1\\n' > "$TEST_ROOT/tvconf/global.conf"; exit 0 ;;
passwd) [ -f "$TEST_ROOT/gui-started" ] && [ -f "$TEST_ROOT/info-seen" ] || exit 98; printf '%s' "$2" > "$TEST_ROOT/password-set"; printf '%s\\n' "$MOCK_PASSWORD_OUTPUT"; exit "$MOCK_PASSWORD_RC" ;;
info) [ -f "$TEST_ROOT/gui-started" ] || exit 98; touch "$TEST_ROOT/info-seen"; count=0; [ ! -f "$TEST_ROOT/info-count" ] || count=$(cat "$TEST_ROOT/info-count"); count=$((count + 1)); printf '%s' "$count" > "$TEST_ROOT/info-count"; if [ "$count" -le "$MOCK_INFO_AFTER" ]; then exit 0; fi; printf '%s\\n' "$MOCK_INFO"; exit "$MOCK_INFO_RC" ;;
*) exit 99 ;;
esac''',
                'openssl': 'if [ "$MOCK_OPENSSL_RC" != 0 ]; then exit "$MOCK_OPENSSL_RC"; fi\nprintf Ab12Cd34',
                'ip': 'if [ "$MOCK_IP" = yes ]; then printf "2: eth0 inet 192.0.2.10/24 scope global eth0\\n"; fi',
                'sleep': ':',
                'pgrep': 'if [ "$MOCK_DESKTOP" = yes ]; then printf 123; fi',
                'pkill': '[ "$1 $2" = "-u admin" ] || exit 99\nprintf stopped > "$TEST_ROOT/gui-stopped"',
                'runuser': '[ -f "$TEST_ROOT/gui-stopped" ] || exit 99\nprintf started > "$TEST_ROOT/gui-started"',
                'systemctl': '''printf '%s\\n' "$1" >> "$TEST_ROOT/service-events"
if [ "$1" = restart ]; then
    grep -Fqx '[int32] EulaAccepted = 1' "$TEST_ROOT/tvconf/global.conf"
fi''',
                'chown': '[ "$1" = root:admin ] || exit 99\nprintf root:admin > "$TEST_ROOT/owner-request"',
            }
            for name, body in commands.items():
                target = bindir / name
                target.write_text('#!/bin/sh\nset -eu\n' + body + '\n')
                target.chmod(0o755)
            env = dict(os.environ, PATH=str(bindir) + ':' + os.environ['PATH'],
                       TEST_ROOT=tmp, MOCK_INFO=info, MOCK_INFO_RC=str(info_rc), MOCK_INFO_AFTER=str(info_after),
                       MOCK_PASSWORD_RC=str(password_rc), MOCK_PASSWORD_OUTPUT=password_output, MOCK_OPENSSL_RC=str(openssl_rc),
                       MOCK_IP='yes' if ip else 'no', MOCK_DESKTOP='yes' if desktop else 'no')
            result = subprocess.run(['bash', str(script)], env=env, capture_output=True, timeout=30)
            txt = root / 'output/teamviewer.txt'
            self.assertTrue(txt.is_file())
            self.assertEqual(txt.stat().st_mode & 0o777, 0o640)
            self.assertEqual((root / 'owner-request').read_text(), 'root:admin')
            self.assertFalse(txt.with_suffix('.txt.tmp').exists())
            content = txt.read_text()
            self.assertNotIn(b'Ab12Cd34', result.stdout + result.stderr)
            if success:
                self.assertEqual(result.returncode, 0)
                self.assertEqual((root / 'service-events').read_text().splitlines()[:2], ['restart', 'is-active'])
                self.assertIn('TeamViewer ID: 123456789\n', content)
                self.assertIn('IP locale: 192.0.2.10', content)
                self.assertIn('Password: ' + (root / 'password-set').read_text(), content)
            else:
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn('Password:', content)
                self.assertNotIn('Ab12Cd34', content)
                self.assertNotIn('inizializzazione in corso', content)
            return content

    def test_no_desktop_no_credentials(self):
        self.run_case(desktop=False)

    def test_vendor_stop_does_not_propagate_to_ibs(self):
        unit = configparser.ConfigParser(interpolation=None)
        unit.read(PROJECT / 'config/includes.chroot/etc/systemd/system/ibs-remote.service')
        dependencies = unit['Unit']
        self.assertIn('teamviewerd.service', dependencies['Wants'].split())
        self.assertIn('teamviewerd.service', dependencies['After'].split())
        self.assertIn('live-config.service', dependencies['After'].split())
        for kind in ('Requires', 'BindsTo', 'PartOf'):
            self.assertNotIn('teamviewerd.service', dependencies.get(kind, '').split())

    def test_success(self):
        self.run_case(success=True)

    def test_eula_before_daemon_start(self):
        self.run_case(eula=False, success=True)

    def test_id_arrives_after_sixty_polls(self):
        self.run_case(info_after=65, success=True)

    def test_ansi_spaces_cr(self):
        self.run_case(info='version\n  \x1b[1;32mTeamViewer ID:\x1b[0m 123 456 789\r\nstatus', success=True)

    def test_reject_invalid_info(self):
        for info in ('TeamViewer ID: 123abc', 'TeamViewer ID: 123 456 trailing',
                     'TeamViewer ID: 0000', 'TeamViewer ID: not found', '',
                     'prefix TeamViewer ID: 123456789',
                     'TeamViewer ID: 123456789\nTeamViewer ID: 987654321'):
            with self.subTest(info=repr(info)):
                self.run_case(info=info)

    def test_info_failed_with_numeric_output(self):
        self.run_case(info_rc=1)

    def test_password_failed(self):
        self.run_case(password_rc=1)

    def test_password_rejected_with_success_exit(self):
        for response in ("password too short - use at least 8 characters [E11]",
                         "password not accepted - illegal char detected [E13]",
                         "passwort invalid - validation failed [E14]",
                         "unknown response", ""):
            with self.subTest(response=response):
                self.run_case(password_output=response)

    def test_unexpected_exit(self):
        self.assertIn('errore imprevisto', self.run_case(openssl_rc=7))

    def test_no_ip(self):
        self.run_case(ip=False)

if __name__ == '__main__':
    unittest.main(verbosity=2)
