#!/usr/bin/env python3
"""Exercise QEMU fdsets on disposable regular files and file-backed loop devices.
Requires root for loop setup. Never selects or opens a physical disk.
"""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'config/includes.chroot/usr/local/lib'))
from ibs2.vm import command, VARS

def request(path, name, arguments=None):
    with socket.socket(socket.AF_UNIX) as sock:
        sock.settimeout(10)
        sock.connect(str(path))
        stream = sock.makefile('rwb', buffering=0)
        stream.readline()
        for cmd in [{'execute': 'qmp_capabilities'}, {'execute': name, 'arguments': arguments or {}}]:
            stream.write(json.dumps(cmd).encode() + b'\n')
            while True:
                result = json.loads(stream.readline())
                if 'return' in result or 'error' in result:
                    break
            if 'error' in result:
                raise RuntimeError(result)
        return result['return']

def test(kind, sector):
    with tempfile.TemporaryDirectory(prefix='block-test-', dir=ROOT / '.build') as folder:
        work = Path(folder)
        os.chown(work, 1000, 1000)
        fixture = work / 'fixture.raw'
        fixture.write_bytes(b'\0' * (8 * 1024 * 1024))
        loop = None
        child = None
        fds = []
        try:
            if kind == 'block':
                loop = subprocess.check_output(['losetup', '--find', '--show', '--sector-size', str(sector), str(fixture)], text=True).strip()
                # The only block path we ever open is the freshly allocated loop.
                assert loop.startswith('/dev/loop')
            path = loop or str(fixture)
            fds = [os.open(path, os.O_RDWR | os.O_DIRECT | (os.O_EXCL if loop else 0))]
            fds.append(os.open(path, os.O_RDONLY | os.O_DIRECT))
            shutil.copyfile(VARS, work / 'OVMF_VARS.fd')
            os.chown(work / 'OVMF_VARS.fd', 1000, 1000)
            args = command(work, [(fds[0], {'_probe_fd': fds[1], 'log-sec': sector, 'phy-sec': sector})],
                           iso=ROOT / 'config/includes.chroot/opt/ibs/iso/IBS-WinRE.iso',
                           display='none', memory=128, acceleration='tcg')
            args += ['-S', '-qmp', f'unix:{work / "qmp.sock"},server=on,wait=off']
            def drop():
                os.setgroups([])
                os.setgid(1000)
                os.setuid(1000)
            with (work / 'qemu.log').open('wb') as log:
                child = subprocess.Popen(args, pass_fds=fds, preexec_fn=drop, stdout=log, stderr=log)
            for _ in range(100):
                if child.poll() is not None:
                    raise RuntimeError((work / 'qemu.log').read_text())
                if (work / 'qmp.sock').exists():
                    break
                time.sleep(.1)
            disks = request(work / 'qmp.sock', 'query-block')
            disk = next(d for d in disks if d['device'] == 'physical0')
            assert disk['inserted']['ro'] is False
            result = request(work / 'qmp.sock', 'human-monitor-command',
                             {'command-line': 'qemu-io physical0 "write -P 90 0 4096"'})
            if result and ('Error' in result or 'not found' in result):
                raise RuntimeError(result)
            request(work / 'qmp.sock', 'human-monitor-command', {'command-line': 'qemu-io physical0 "flush"'})
            request(work / 'qmp.sock', 'quit')
            child.wait(timeout=10)
            assert fixture.read_bytes()[:4096] == b'Z' * 4096
            print(f'PASS: {kind}, settori {sector}, QEMU uid 1000, fdset RW e scrittura 4096 byte verificata')
        finally:
            if child and child.poll() is None:
                child.terminate()
                child.wait(timeout=10)
            for fd in fds:
                os.close(fd)
            if loop:
                subprocess.run(['losetup', '--detach', loop], check=True)

if __name__ == '__main__':
    if os.geteuid() != 0:
        raise SystemExit('Root richiesto solo per dispositivi loop temporanei')
    test('file', 512)
    test('block', 512)
    test('block', 4096)
