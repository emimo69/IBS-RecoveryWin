#!/usr/bin/env python3
"""Launcher tests with isolated HOME, XDG and metadata mocks; no real GUI/TXT."""
import configparser
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path('/opt/ibs-recoverywin-1.0')
INCLUDES = ROOT / 'config/includes.chroot'

class LauncherTests(unittest.TestCase):
    def run_case(self, relative='Scrivania', metadata_failures=0):
        with tempfile.TemporaryDirectory(prefix='.launcher-test-', dir=ROOT) as tmp:
            case = Path(tmp)
            home = case / 'home admin'
            home.mkdir()
            bindir = case / 'bin'
            bindir.mkdir()
            assets = case / 'assets'
            assets.mkdir()
            template = assets / 'teamviewer-assistenza.desktop'
            template.write_text((INCLUDES / 'usr/share/ibs/teamviewer-assistenza.desktop').read_text())
            source = (INCLUDES / 'usr/local/bin/ibs-desktop-launcher').read_text().replace('/usr/share/ibs', str(assets))
            script = case / 'launcher'
            script.write_text(source)
            commands = {
                'id': 'printf admin',
                'xdg-user-dirs-update': '[ -d "$HOME" ]',
                'xdg-user-dir': 'printf "%s/%s\\n" "$HOME" "$MOCK_DESKTOP"',
                'gio': '''[ "$1" = set ] && [ "$2" = -t ] && [ "$3" = string ]
[ "$5" = metadata::xfce-exe-checksum ] || exit 90
count=0
if [ -f "$TEST_CASE/gio-count" ]; then read -r count < "$TEST_CASE/gio-count"; fi
count=$((count+1)); printf '%s\\n' "$count" > "$TEST_CASE/gio-count"
[ "$count" -gt "$MOCK_METADATA_FAILURES" ] || exit 1
printf '%s' "$6" > "$TEST_CASE/checksum"
''',
                'sleep': ':',
                'mousepad': 'printf "%s" "$1" > "$TEST_CASE/mousepad-target"',
            }
            for name, body in commands.items():
                p = bindir / name
                p.write_text('#!/bin/sh\nset -eu\n' + body + '\n')
                p.chmod(0o755)
            env = dict(os.environ, HOME=str(home), TEST_CASE=tmp, MOCK_DESKTOP=relative,
                       MOCK_METADATA_FAILURES=str(metadata_failures),
                       PATH=str(bindir) + ':' + os.environ['PATH'])
            result = subprocess.run(['sh', str(script)], env=env, capture_output=True, timeout=10)
            launcher = home / relative / 'teamviewer-assistenza.desktop'
            self.assertEqual(result.returncode, 0)
            self.assertEqual(launcher.stat().st_mode & 0o777, 0o755)
            self.assertEqual((case/'checksum').read_text(), hashlib.sha256(launcher.read_bytes()).hexdigest())
            config = configparser.ConfigParser(interpolation=None)
            config.read(launcher)
            entry = config['Desktop Entry']
            self.assertEqual(entry['Name'], 'TeamViewer ID e Password')
            self.assertEqual(entry['Exec'], 'mousepad /mnt/teamviewer.txt')
            subprocess.run(entry['Exec'].split(), env=env, check=True)
            self.assertEqual((case/'mousepad-target').read_text(), '/mnt/teamviewer.txt')
            # Repeated invocation preserves the valid launcher/checksum.
            again = subprocess.run(['sh', str(script)], env=env, capture_output=True, timeout=10)
            self.assertEqual(again.returncode, 0)

    def test_italian_desktop(self):
        self.run_case()

    def test_custom_desktop_with_spaces(self):
        self.run_case('Desktop personalizzato')

    def test_metadata_service_delayed(self):
        self.run_case(metadata_failures=3)

if __name__ == '__main__':
    unittest.main(verbosity=2)
