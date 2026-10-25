#!/usr/bin/env python3
"""Offline source preflight. --host adds read-only tool/APT/CPU checks, never boots."""
import argparse
import configparser
from pathlib import Path
import re
import shutil
import subprocess

PROJECT = Path('/opt/ibs-recoverywin-1.0')
ROOT = PROJECT / 'config/includes.chroot'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--host', action='store_true')
args = parser.parse_args()

def need(condition, message):
    if not condition:
        raise SystemExit('ERRORE preflight: ' + message)

def text(path):
    return (PROJECT / path).read_text()

def entry(path, section):
    config = configparser.ConfigParser(interpolation=None)
    config.read(ROOT / path)
    return config[section]

packages = set()
for path in (PROJECT / 'config/package-lists').glob('*.list.chroot'):
    packages.update(line.strip() for line in path.read_text().splitlines()
                    if line.strip() and not line.startswith('#'))
required = {'linux-image-amd64', 'live-boot', 'live-config', 'live-config-systemd',
            'systemd-sysv', 'xfce4', 'lightdm', 'lightdm-gtk-greeter', 'xorg',
            'openssh-server', 'sudo', 'locales', 'keyboard-configuration',
            'network-manager', 'network-manager-gnome', 'curl', 'ca-certificates',
            'openssl', 'iproute2', 'mousepad', 'conky-std', 'gvfs',
            'libglib2.0-bin', 'xdg-user-dirs'}
need(required <= packages, 'pacchetti essenziali mancanti: ' + ', '.join(sorted(required-packages)))
# user-setup is a Recommends of live-config 11.0.5, essential to creation of admin.
need('user-setup' in packages or 'LB_APT_RECOMMENDS="true"' in text('config/common'),
     'user-setup non garantito: esplicitarlo o mantenere APT Recommends')
for path in ('auto/config', 'config/binary'):
    content = text(path)
    for token in ('boot=live components', 'username=admin', 'locales=it_IT.UTF-8',
                  'keyboard-layouts=it', 'timezone=Europe/Rome'):
        need(token in content, path + ': manca ' + token)
need('LB_DISTRIBUTION="trixie"' in text('config/bootstrap'), 'distribuzione errata')
need('LB_ARCHITECTURE="amd64"' in text('config/bootstrap'), 'architettura errata')
need('LB_INITRAMFS="live-boot"' in text('config/common'), 'initramfs non live-boot')
need('LB_DEBIAN_INSTALLER="none"' in text('config/binary'), 'installer non disabilitato')
admin = text('config/includes.chroot/lib/live/config/0990-ibs-admin')
need("printf 'admin:admin\\n' | chpasswd" in admin, 'password admin non impostata')
need('usermod -aG sudo admin' in admin and 'ssh-keygen -A' in admin, 'sudo/chiavi SSH mancanti')
lightdm = entry('etc/lightdm/lightdm.conf.d/90-ibs.conf', 'Seat:*')
need(lightdm['autologin-user'] == 'admin' and lightdm['user-session'] == 'xfce', 'autologin errato')
ssh = (ROOT / 'etc/ssh/sshd_config.d/00-ibs.conf').read_text()
need('PasswordAuthentication yes' in ssh and 'AllowUsers admin' in ssh, 'accesso SSH errato')
hook = text('config/hooks/normal/0100-teamviewer.hook.chroot')
for token in ('https://download.teamviewer.com/download/linux/teamviewer_amd64.deb',
              'dpkg-deb -f', '= amd64', 'apt-get install -y /tmp/teamviewer_amd64.deb',
              'systemctl enable ssh.service NetworkManager.service teamviewerd.service ibs-remote.service'):
    need(token in hook, 'hook installazione incompleto: ' + token)
unit = entry('etc/systemd/system/ibs-remote.service', 'Unit')
need('live-config.service' in unit['After'], 'servizio remoto prima della creazione utente')
need('teamviewerd.service' in unit['Wants'], 'daemon TeamViewer non avviato')
need('teamviewerd.service' not in unit.get('Requires', ''), 'Requires ferma IBS durante passwd vendor')
for launcher, command in (('ibs-remote', 'conky -c /etc/conky/ibs.conf'),
                          ('ibs-teamviewer', 'teamviewer'),
                          ('ibs-desktop-launcher', '/usr/local/bin/ibs-desktop-launcher')):
    need(entry('etc/xdg/autostart/' + launcher + '.desktop', 'Desktop Entry')['Exec'] == command,
         'autostart incompleto: ' + launcher)
for path in (ROOT / 'lib/live/config/0990-ibs-admin', ROOT / 'usr/local/sbin/ibs-remote',
             ROOT / 'usr/local/bin/ibs-desktop-launcher', PROJECT / 'auto/config',
             PROJECT / 'config/hooks/normal/0100-teamviewer.hook.chroot'):
    need(path.stat().st_mode & 0o111, 'script non eseguibile: ' + str(path))
    subprocess.run(['sh', '-n', str(path)], check=True)
print('OK: pacchetti, boot admin/italiano, live-config, login, SSH, TeamViewer, dipendenze servizio e autostart (statico).')
if args.host:
    for tool in ('lb', 'qemu-system-x86_64', 'ssh'):
        print(('PRESENTE: ' if shutil.which(tool) else 'MANCANTE: ') + tool)
    if shutil.which('apt-cache'):
        result = subprocess.run(['apt-cache', 'show', *sorted(packages)], capture_output=True, text=True)
        known = set(re.findall(r'^Package: (.+)$', result.stdout, re.M))
        need(packages <= known, 'metadati APT mancanti: ' + ', '.join(sorted(packages-known)))
        print('OK: nomi pacchetti presenti nei metadati APT locali; nessuna risoluzione/installazione o verifica rete.')
    flags = Path('/proc/cpuinfo').read_text()
    exposed = bool(re.search(r'\b(vmx|svm)\b', flags))
    print('Estensioni vmx/svm esposte: ' + ('sì' if exposed else 'no'))
    print('/dev/kvm presente: ' + ('sì' if Path('/dev/kvm').exists() else 'no'))
    for name in ('kvm_intel', 'kvm_amd'):
        nested = Path('/sys/module') / name / 'parameters/nested'
        print(name + ' nested: ' + (nested.read_text().strip() if nested.exists() else 'parametro assente'))
    print('Nessuna VM, ioctl KVM, immagine esterna, attivazione timer o modifica al sistema eseguita.')
