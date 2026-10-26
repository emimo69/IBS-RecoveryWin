#!/usr/bin/env python3
"""One bounded firmware-only TCG boot. No caller-supplied media or devices."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import stat
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
CODE = Path('/usr/share/OVMF/OVMF_CODE_4M.fd')
VARS = Path('/usr/share/OVMF/OVMF_VARS_4M.fd')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def firmware(path, size):
    for component in (path, *path.parents):
        if component.is_symlink():
            raise ValueError('Symlink firmware path')
    if not stat.S_ISREG(path.stat().st_mode) or path.stat().st_size != size:
        raise ValueError('Unexpected firmware file')
    if path.read_bytes()[40:44] != b'_FVH':
        raise ValueError('Missing FV signature')


def main():
    if len(sys.argv) != 1:
        raise RuntimeError('No arguments accepted: firmware-only fixed configuration')
    if os.geteuid() == 0 or Path.cwd() != ROOT:
        raise RuntimeError('Run unprivileged from project root')
    firmware(CODE, 3653632)
    firmware(VARS, 540672)
    build = ROOT / '.build'
    if build.is_symlink():
        raise RuntimeError('Symlink build directory')
    build.mkdir(exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix='r7-', dir=build))
    before = {str(p): digest(p) for p in (CODE, VARS)}
    copy = folder / 'VARS.fd'
    shutil.copyfile(VARS, copy)
    copy.chmod(0o600)
    qmp = folder / 'qmp.sock'
    argv = ['qemu-system-x86_64', '-machine', 'q35', '-accel', 'tcg',
            '-m', '256', '-no-user-config', '-nodefaults', '-nic', 'none',
            '-display', 'none', '-device', 'VGA', '-monitor', 'none',
            '-serial', 'file:' + str(folder / 'serial.log'), '-S',
            '-drive', f'if=pflash,format=raw,readonly=on,file={CODE}',
            '-drive', f'if=pflash,format=raw,file={copy}',
            '-qmp', f'unix:{qmp},server=on,wait=off']
    report = dict(argv=argv, before=before, guest_disks=0, network=False,
                  version=subprocess.check_output([argv[0], '--version'], text=True,
                                                  timeout=5).splitlines()[0])
    started = time.monotonic()
    proc = None
    conn = None
    # Hard watchdog includes launch, observation and cleanup; never exceeds 10 min.
    def expired(signum, frame):
        raise TimeoutError('R7 total watchdog (120 seconds)')
    old = signal.signal(signal.SIGALRM, expired)
    signal.alarm(120)
    try:
        with (folder / 'qemu.log').open('wb') as log:
            proc = subprocess.Popen(argv, stdout=log, stderr=log)
            report['pid'] = proc.pid
            conn = socket.socket(socket.AF_UNIX)
            conn.settimeout(3)
            deadline = time.monotonic() + 15
            while True:
                try:
                    conn.connect(str(qmp))
                    break
                except (FileNotFoundError, ConnectionRefusedError):
                    if proc.poll() is not None or time.monotonic() >= deadline:
                        raise RuntimeError('QEMU/QMP unavailable')
                    time.sleep(0.1)
            stream = conn.makefile('rwb', buffering=0)
            report['greeting'] = json.loads(stream.readline())
            def request(name, arguments=None):
                stream.write((json.dumps(dict(execute=name, arguments=arguments or {},
                                              id=name)) + '\n').encode())
                while True:
                    reply = json.loads(stream.readline())
                    if reply.get('id') == name:
                        if 'error' in reply:
                            raise RuntimeError(reply)
                        return reply['return']
            request('qmp_capabilities')
            report['paused'] = request('query-status')
            blocks = report['blocks'] = request('query-block')
            expected = {str(CODE): True, str(copy): False}
            actual = {b['inserted']['file']: b['inserted']['ro'] for b in blocks}
            if len(blocks) != 2 or actual != expected or report['paused']['running']:
                raise RuntimeError('Unexpected backends/state')
            report['pci'] = request('query-pci')
            if 'ethernet' in json.dumps(report['pci']).lower():
                raise RuntimeError('Unexpected network device')
            request('cont')
            time.sleep(45)
            report['running'] = request('query-status')
            request('screendump', {'filename': str(folder / 'screen.ppm')})
            request('quit')
    except BaseException as exc:
        report['error'] = repr(exc)
    finally:
        # Cancel watchdog before cleanup: SIGALRM must not interrupt process reap.
        signal.alarm(0)
        if proc is not None:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
            report['returncode'] = proc.returncode
            report['reaped'] = proc.poll() is not None
        if conn is not None:
            conn.close()
        signal.signal(signal.SIGALRM, old)
        report['duration_seconds'] = round(time.monotonic() - started, 3)
        report['after'] = {str(p): digest(p) for p in (CODE, VARS)}
        report['hashes_unchanged'] = before == report['after']
        (folder / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
        print(folder / 'result.json', flush=True)
    if report.get('error') or not report['hashes_unchanged']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
