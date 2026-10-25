#!/usr/bin/env python3
"""Guest-only diagnosis. JSON contains fixed statuses/flags, never credentials or raw logs."""
import argparse
import hashlib
import stat
import re
import json
import os
from pathlib import Path
import pwd
import shutil
import subprocess
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--probe-launcher', action='store_true')
parser.add_argument('--probe-services', action='store_true')
parser.add_argument('--probe-dependency-fix', action='store_true')
args = parser.parse_args()
if 'boot=live' not in Path('/proc/cmdline').read_text().split() or os.getuid() != pwd.getpwnam('admin').pw_uid:
    raise SystemExit('Run only as admin inside the IBS Live guest, never on the development server.')

def command(argv, env=None):
    return subprocess.run(argv, capture_output=True, text=True, env=env, timeout=30)

report = {'guest_guard': True}
for unit in ('teamviewerd.service', 'ibs-remote.service'):
    fields = ('ActiveState', 'SubState', 'Result', 'ExecMainStatus', 'NRestarts',
              'ActiveEnterTimestampMonotonic', 'InactiveEnterTimestampMonotonic')
    result = command(['systemctl', 'show', unit, '--property=' + ','.join(fields)])
    # Only known finite states and integer fields are admitted.
    safe = {}
    for line in result.stdout.splitlines():
        key, _, value = line.partition('=')
        if key in fields and (value.isdigit() or value in
            {'active','inactive','failed','activating','deactivating','dead','running','exited',
             'start','start-pre','stop','stop-sigterm','success','exit-code','signal','timeout','dependency'}):
            safe[key] = value
    report[unit] = safe
# Inspect systemd lifecycle events privately and emit only fixed labels/timestamps.
r = command(['sudo','-n','journalctl','-b','-u','teamviewerd.service','-u','ibs-remote.service','-o','json','--no-pager'])
events = []
for line in r.stdout.splitlines():
    try:
        row = json.loads(line)
    except ValueError:
        continue
    if row.get('SYSLOG_IDENTIFIER') != 'systemd':
        continue
    unit = row.get('UNIT', '')
    if unit not in ('teamviewerd.service','ibs-remote.service'):
        continue
    msg = row.get('MESSAGE','')
    label = next((tag for prefix,tag in [('Starting ', 'starting'), ('Started ', 'started'),
                 ('Stopping ', 'stopping'), ('Stopped ', 'stopped'), ('Dependency failed', 'dependency_failed')]
                 if msg.startswith(prefix)), None)
    if label is None and ('Failed with result' in msg or 'Main process exited' in msg or 'Control process exited' in msg):
        label = 'failure'
    if label:
        events.append({'unit':unit,'event':label,'monotonic_us':row.get('__MONOTONIC_TIMESTAMP')})
report['lifecycle_events'] = events
report['journal_query_rc'] = r.returncode
home = Path.home()
p = command(['xdg-user-dir','DESKTOP'])
desktop = Path(p.stdout.strip()) if p.returncode == 0 and p.stdout.strip() else home
report['desktop_kind'] = 'home' if desktop == home else 'Scrivania' if desktop == home/'Scrivania' else 'Desktop' if desktop == home/'Desktop' else 'other'
report['user_dirs_config_present'] = (home/'.config/user-dirs.dirs').is_file()
report['desktop_directory_present'] = desktop.is_dir()
launcher = desktop/'teamviewer-assistenza.desktop'
report['launcher_present'] = launcher.is_file()
report['launcher_executable'] = os.access(launcher, os.X_OK)
report['template_present'] = Path('/usr/share/ibs/teamviewer-assistenza.desktop').is_file()
report['launcher_metadata_matches_checksum'] = False
txt=Path('/mnt/teamviewer.txt')
report['txt_readable'] = os.access(txt, os.R_OK)
report['txt_regular'] = txt.is_file() and not txt.is_symlink()
if txt.exists():
    st=txt.stat()
    report['txt_mode_0640'] = stat.S_IMODE(st.st_mode) == 0o640
    report['txt_root_admin_owner'] = st.st_uid == 0 and st.st_gid == pwd.getpwnam('admin').pw_gid
report['ssh_active'] = command(['systemctl','is-active','ssh.service']).returncode == 0
report['locale_italian'] = command(['locale']).stdout.splitlines().count('LANG=it_IT.UTF-8') == 1
report['launcher_script_executable'] = os.access('/usr/local/bin/ibs-desktop-launcher', os.X_OK)
report['autostart_present'] = Path('/etc/xdg/autostart/ibs-desktop-launcher.desktop').is_file()
report['commands_present'] = {name:shutil.which(name) is not None for name in ('xdg-user-dir','xdg-user-dirs-update','gio','mousepad','sha256sum')}
proc = command(['pgrep','-u',str(os.getuid()),'-x','xfce4-session'])
session_env = None
for pid in proc.stdout.split():
    if pid.isdigit():
        try:
            env = dict(item.split('=',1) for item in Path('/proc',pid,'environ').read_text().split('\0') if '=' in item)
            session_env = env
            break
        except (OSError, ValueError):
            pass
report['xfce_session_found'] = session_env is not None
if session_env is not None:
    report['session_display_present'] = bool(session_env.get('DISPLAY'))
    report['session_bus_present'] = bool(session_env.get('DBUS_SESSION_BUS_ADDRESS'))
    report['session_desktop_is_xfce'] = session_env.get('XDG_CURRENT_DESKTOP','').upper() == 'XFCE'
if launcher.is_file() and session_env is not None:
    metadata=command(['gio','info','-a','metadata::xfce-exe-checksum',str(launcher)], env=session_env)
    values=re.findall(r'metadata::xfce-exe-checksum: ([0-9a-f]{64})',metadata.stdout)
    report['launcher_metadata_matches_checksum'] = values == [hashlib.sha256(launcher.read_bytes()).hexdigest()]
    report['launcher_exec_correct'] = 'Exec=mousepad /mnt/teamviewer.txt' in launcher.read_text()
if args.probe_launcher and session_env is not None:
    r = command(['/usr/local/bin/ibs-desktop-launcher'], env=session_env)
    report['launcher_probe_rc'] = r.returncode
    report['launcher_probe_permission_error'] = 'Permission denied' in r.stderr or 'Permesso negato' in r.stderr
    report['launcher_probe_metadata_error'] = 'metadata' in r.stderr.lower()
    after = command(['xdg-user-dir','DESKTOP'], env=session_env)
    target = Path(after.stdout.strip())/'teamviewer-assistenza.desktop'
    report['launcher_after_probe_executable'] = os.access(target, os.X_OK)
    # Exercise the requested Exec without capturing/rendering document contents.
    # No screenshots and no stdout/stderr from Mousepad are retained.
    if target.is_file() and 'Exec=mousepad /mnt/teamviewer.txt' in target.read_text():
        app=subprocess.Popen(['mousepad','/mnt/teamviewer.txt'],env=session_env,
                             stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        time.sleep(2)
        report['mousepad_exec_accepted'] = app.poll() in (None, 0)
        report['mousepad_process_present'] = command(['pgrep','-u',str(os.getuid()),'-x','mousepad']).returncode == 0
# Minimal guest-only probe: start vendor daemon separately, then retry IBS.
# No TeamViewer info/password command output is read or exposed.
if args.probe_services:
    r = command(['sudo','-n','systemctl','start','teamviewerd.service'])
    report['standalone_daemon_start_rc'] = r.returncode
    r = command(['systemctl','is-active','teamviewerd.service'])
    report['standalone_daemon_active'] = r.returncode == 0
    r = command(['sudo','-n','systemctl','start','--no-block','ibs-remote.service'])
    report['ibs_retry_request_rc'] = r.returncode
    for attempt in range(6):
        r = command(['systemctl','is-active','ibs-remote.service'])
        if r.stdout.strip() in ('active','failed'):
            break
        time.sleep(2)
    report['ibs_retry_active'] = r.returncode == 0
    report['ibs_retry_failed'] = r.stdout.strip() == 'failed'
# Confirm the dependency/CLI stop interaction in this disposable guest only.
unit_path=Path('/etc/systemd/system/ibs-remote.service')
vendor=Path('/opt/teamviewer/tv_bin/script/tvw_extra')
report['vendor_password_stops_daemon'] = "Run_Daemon 'stop'" in vendor.read_text()
report['ibs_requires_daemon'] = 'Requires=teamviewerd.service' in unit_path.read_text()
if args.probe_dependency_fix and report['vendor_password_stops_daemon'] and report['ibs_requires_daemon']:
    patch = "from pathlib import Path; p=Path('/etc/systemd/system/ibs-remote.service'); s=p.read_text(); assert 'Requires=teamviewerd.service' in s; p.write_text(s.replace('Requires=teamviewerd.service','Wants=teamviewerd.service'))"
    report['guest_dependency_patch_rc'] = command(['sudo','-n','python3','-c',patch]).returncode
    report['guest_daemon_reload_rc'] = command(['sudo','-n','systemctl','daemon-reload']).returncode
    command(['sudo','-n','systemctl','start','--no-block','ibs-remote.service'])
    for attempt in range(30):
        r=command(['systemctl','is-active','ibs-remote.service'])
        if r.stdout.strip() in ('active','failed'):
            break
        time.sleep(2)
    report['patched_ibs_active'] = r.returncode == 0
    report['patched_ibs_activating'] = r.stdout.strip() == 'activating'
    report['patched_daemon_active'] = command(['systemctl','is-active','teamviewerd.service']).returncode == 0
print(json.dumps(report, sort_keys=True, indent=2))
