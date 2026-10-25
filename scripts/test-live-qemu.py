#!/usr/bin/env python3
"""One-shot diskless TCG test; private outputs contain status only, never TXT."""
import datetime
import argparse
import json
import os
from pathlib import Path
import pwd
import signal
import socket
import subprocess
import time

root = Path('/opt/ibs-recoverywin-1.0')
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('iso', type=Path, help='Existing ISO inside this project; never a disk image')
args=parser.parse_args()
iso=args.iso.resolve()
if not iso.is_relative_to(root) or iso.suffix != '.iso':
    raise SystemExit('Only a project ISO is allowed.')
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
prefix = root / '.build' / ('QEMU-LIVE-' + stamp)
result_path = Path(str(prefix) + '-result.json')
qmp_path = Path(str(prefix) + '.sock')
askpass = Path(str(prefix) + '-askpass')
knownhosts = Path(str(prefix) + '-knownhosts')
report = {'started_utc': stamp, 'mode': 'TCG, no disks, only read-only ISO',
          'ssh_port_localhost': 22221, 'vnc_port_localhost': 5911,
          'gui_observed': False, 'teamviewer_remote_connection_tested': False}
qemu = None
def interrupted(signum, frame):
    raise SystemExit(128 + signum)
signal.signal(signal.SIGTERM, interrupted)
signal.signal(signal.SIGINT, interrupted)
os.umask(0o077)

def qmp(command):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as conn:
        conn.settimeout(5)
        conn.connect(str(qmp_path))
        stream = conn.makefile('rwb', buffering=0)
        stream.readline()
        stream.write(b'{"execute":"qmp_capabilities"}\n')
        while b'"return"' not in stream.readline():
            pass
        stream.write(json.dumps({'execute': command}).encode() + b'\n')
        while True:
            line = stream.readline()
            if not line:
                return None
            obj = json.loads(line)
            if 'return' in obj or 'error' in obj:
                return obj

ssh_base = ['ssh', '-T', '-p', '22221', '-o', 'ConnectTimeout=5',
            '-o', 'ConnectionAttempts=1', '-o', 'StrictHostKeyChecking=accept-new',
            '-o', 'UserKnownHostsFile=' + str(knownhosts), '-o', 'LogLevel=ERROR',
            '-o', 'PubkeyAuthentication=no', '-o', 'PreferredAuthentications=password',
            '-o', 'NumberOfPasswordPrompts=1', 'admin@127.0.0.1']
ssh_env = dict(os.environ, SSH_ASKPASS=str(askpass), SSH_ASKPASS_REQUIRE='force', DISPLAY='unused:0')

def ssh(command, timeout=30):
    return subprocess.run(ssh_base + [command], stdin=subprocess.DEVNULL,
                          env=ssh_env, capture_output=True, text=True,
                          start_new_session=True, timeout=timeout)

try:
    if not iso.is_file():
        raise RuntimeError('ISO missing')
    for port in (22221, 5911):
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', port))
    user = pwd.getpwnam('utente')
    if user.pw_uid == 0:
        raise RuntimeError('QEMU must run unprivileged')
    askpass.write_text('#!/bin/sh\nprintf "%s\\n" admin\n')
    askpass.chmod(0o700)
    command = ['qemu-system-x86_64', '-no-user-config', '-name', 'IBS-TEST-1.0',
               '-accel', 'tcg', '-cpu', 'max', '-smp', '2', '-m', '2048',
               '-cdrom', str(iso), '-boot', 'order=d',
               '-nic', 'user,model=virtio-net-pci,hostfwd=tcp:127.0.0.1:22221-:22',
               '-display', 'vnc=127.0.0.1:11', '-serial', 'none',
               '-qmp', 'unix:' + str(qmp_path) + ',server=on,wait=off',
               '-no-reboot']
    report['qemu_command'] = command
    with open(str(prefix) + '-qemu.log', 'xb') as output:
        qemu = subprocess.Popen(command, cwd=root, stdin=subprocess.DEVNULL,
                                stdout=output, stderr=output, user=user.pw_uid,
                                group=user.pw_gid, extra_groups=[], start_new_session=True)
    report['qemu_pid']=qemu.pid
    print('QEMU started on specified ISO; waiting boot.', flush=True)
    time.sleep(12)
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as conn:
        conn.settimeout(5); conn.connect(str(qmp_path)); stream=conn.makefile('rwb',buffering=0); stream.readline()
        for item in ({'execute':'qmp_capabilities'}, {'execute':'human-monitor-command','arguments':{'command-line':'sendkey ret'}}):
            stream.write(json.dumps(item).encode()+b'\n')
            while True:
                reply=json.loads(stream.readline())
                if 'return' in reply or 'error' in reply: break
    deadline = time.monotonic() + 600
    connected = False
    while time.monotonic() < deadline and qemu.poll() is None:
        try:
            check = ssh('id -un', timeout=12)
            if check.returncode == 0 and check.stdout.strip() == 'admin':
                connected = True
                break
        except subprocess.TimeoutExpired:
            pass
        time.sleep(5)
    report['ssh_admin_password_login'] = connected
    if not connected:
        report['outcome'] = 'SSH admin/admin not reached within 600 seconds; boot not confirmed'
        if qemu.poll() is None:
            report['qmp_status'] = qmp('query-status')
        print(report['outcome'], flush=True)
    else:
        print('SSH password authentication admin/admin confirmed.', flush=True)
        # SSH can precede graphical login and XDG/autostart setup.
        deadline=time.monotonic()+180
        while time.monotonic()<deadline:
            gui=ssh('pgrep -u admin -x xfce4-session >/dev/null')
            if gui.returncode == 0:
                time.sleep(25)
                break
            time.sleep(5)
        deadline=time.monotonic()+180
        while time.monotonic()<deadline:
            state=ssh('systemctl is-active ibs-remote.service || true')
            if state.stdout.strip() in ('active','failed'):
                break
            time.sleep(5)
        diagnostic=(root/'scripts/diagnose-live.py').read_text()
        import shlex
        checks=ssh('python3 -c ' + shlex.quote(diagnostic) + ' --probe-launcher', timeout=180)
        report['diagnostic_rc']=checks.returncode
        if checks.returncode == 0:
            report['diagnostic']=json.loads(checks.stdout)
            print(json.dumps(report['diagnostic'],indent=2),flush=True)
        else:
            print('Guest diagnostic failed; no raw output retained.',flush=True)
        report['outcome']='Guest checks completed; GUI and remote TeamViewer not observed'
        # Power off normally if live sudo allows it; QMP fallback in finally.
        ssh('sudo -n systemctl poweroff', timeout=15)
except Exception as exc:
    report['error'] = type(exc).__name__  # no untrusted output/credentials
    print('Test error: ' + type(exc).__name__, flush=True)
finally:
    if qemu is not None:
        if qemu.poll() is None:
            try:
                qmp('system_powerdown')
                qemu.wait(timeout=30)
            except Exception:
                try:
                    qmp('quit')
                    qemu.wait(timeout=10)
                except Exception:
                    os.killpg(qemu.pid, signal.SIGTERM)
                    try:
                        qemu.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        os.killpg(qemu.pid, signal.SIGKILL)
                        qemu.wait(timeout=10)
        report['qemu_exit_code'] = qemu.returncode
        report['vm_stopped'] = qemu.poll() is not None
    report['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    result_path.write_text(json.dumps(report, indent=2) + '\n')
    print('Status report: ' + str(result_path), flush=True)
    print('VM stopped: ' + str(report.get('vm_stopped', 'not started')), flush=True)
