#!/usr/bin/env python3
"""Static checks only: no services, user changes or filesystem mounts."""
from pathlib import Path
import configparser

root = Path('config/includes.chroot')
remote = (root / 'usr/local/sbin/ibs-remote').read_text()
launcher_script = (root / 'usr/local/bin/ibs-desktop-launcher').read_text()
assert 'info=/mnt/teamviewer.txt' in remote
assert 'install -d -m 0755 /mnt' in remote
assert 'chown root:admin "$info.tmp"' in remote
assert 'chmod 0640 "$info.tmp"' in remote
assert 'mv "$info.tmp" "$info"' in remote
assert remote.index("publish 'TeamViewer: inizializzazione") < remote.index('password=')
assert remote.index('teamviewer passwd "$password"') < remote.index('Password: $password')
assert 'IP locale: $ips' in remote and 'ip -o -4 addr show scope global' in remote
assert 'if [ -z "$ips" ]; then' in remote
assert 'if output=$(teamviewer info 2>/dev/null); then' in remote
assert 'trap on_exit EXIT' in remote
assert 'count == 1' in remote
assert 'metadata::xfce-exe-checksum "$checksum"' in launcher_script
assert 'install -m 0755' in launcher_script
assert 'xdg-user-dir DESKTOP' in launcher_script
assert 'sha256sum "$launcher"' in launcher_script
for path in root.rglob('*'):
    if path.is_file():
        assert '/run/ibs/teamviewer.txt' not in path.read_text(), str(path)
launcher = root / 'usr/share/ibs/teamviewer-assistenza.desktop'
assert launcher.stat().st_mode & 0o777 == 0o755
entry = configparser.ConfigParser(interpolation=None)
entry.read(launcher)
assert entry['Desktop Entry']['Name'] == 'TeamViewer ID e Password'
assert entry['Desktop Entry']['Exec'] == 'mousepad /mnt/teamviewer.txt'
assert '/mnt/teamviewer.txt' in (root / 'etc/conky/ibs.conf').read_text()
assert 'printf \'admin:admin\\n\' | chpasswd' in (root / 'lib/live/config/0990-ibs-admin').read_text()
print('OK: percorsi, permessi previsti, pubblicazione e launcher XFCE (controlli statici).')
