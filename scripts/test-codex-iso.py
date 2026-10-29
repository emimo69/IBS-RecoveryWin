#!/usr/bin/env python3
"""Isolated ISO GUI smoke tests: no NIC, no physical disks, private monitor."""
import argparse
import json
import os
import select
from pathlib import Path
import shutil
import socket
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
ISO = ROOT / 'IBS-RecoveryWin-2.1-Codex-amd64.hybrid.iso'


def command(folder, name, arguments=None):
    with socket.socket(socket.AF_UNIX) as connection:
        connection.settimeout(8)
        connection.connect(str(folder / 'qmp.sock'))
        f = connection.makefile('rwb', buffering=0)
        json.loads(f.readline())
        for request in [{'execute': 'qmp_capabilities'},
                        {'execute': name, 'arguments': arguments or {}}]:
            f.write(json.dumps(request).encode() + b'\n')
            while True:
                result = json.loads(f.readline())
                if 'error' in result:
                    raise RuntimeError(result['error'])
                if 'return' in result:
                    break
        return result['return']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['start', 'screen', 'key', 'type', 'stop', 'status'])
    parser.add_argument('--firmware', choices=['bios', 'uefi'], required=True)
    parser.add_argument('--text', default='')
    args = parser.parse_args()
    folder = ROOT / '.build/iso-tests' / args.firmware
    state = folder / 'vm.json'
    name = 'IBS-Codex-ISO-test-' + args.firmware
    if args.action == 'start':
        build = json.loads((ROOT / '.build/remaster-codex/state.json').read_text())
        if build['phase'] != 'BUILT' or not ISO.is_file():
            raise RuntimeError('Candidate not verified')
        folder.mkdir(parents=True, exist_ok=False)
        argv = ['qemu-system-x86_64', '-name', name, '-machine', 'q35,accel=tcg',
                '-cpu', 'max', '-m', '1536', '-smp', '2',
                '-cdrom', str(ISO), '-boot', 'order=d', '-nic', 'none',
                '-display', 'none', '-vga', 'std',
                '-qmp', 'unix:' + str(folder / 'qmp.sock') + ',server=on,wait=off',
                '-serial', 'file:' + str(folder / 'serial.log')]
        if args.firmware == 'uefi':
            code = Path('/usr/share/OVMF/OVMF_CODE_4M.fd')
            variables = Path('/usr/share/OVMF/OVMF_VARS_4M.fd')
            shutil.copyfile(variables, folder / 'OVMF_VARS.fd')
            argv += ['-drive', 'if=pflash,format=raw,readonly=on,file=' + str(code),
                     '-drive', 'if=pflash,format=raw,file=' + str(folder / 'OVMF_VARS.fd')]
        with (folder / 'qemu.log').open('wb') as log:
            proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                    start_new_session=True)
        state.write_text(json.dumps({'pid': proc.pid, 'name': name, 'args': argv,
                                     'started': time.time(), 'physical_disks': False, 'network': False}, indent=2))
        print(json.dumps({'started': True, 'pid': proc.pid, 'firmware': args.firmware}))
        return
    data = json.loads(state.read_text())
    proc = Path('/proc') / str(data['pid']) / 'cmdline'
    if not proc.exists() or name.encode() not in proc.read_bytes().split(b'\0'):
        raise RuntimeError('Expected test VM is not running; no other process touched')
    if args.action == 'screen':
        image = folder / 'screen.ppm'
        command(folder, 'screendump', {'filename': str(image)})
        print(json.dumps({'screen': str(image)}))
    elif args.action == 'key':
        if not all(c.isalnum() or c in '-_' for c in args.text):
            raise RuntimeError('Unexpected key chord')
        command(folder, 'human-monitor-command', {'command-line': 'sendkey ' + args.text})
        print('Key sent to isolated guest')
    elif args.action == 'type':
        for c in args.text:
            if c.isascii() and (c.islower() or c.isdigit()):
                key = c
            else:
                key = {'-': 'slash', '/': 'shift-7', '.': 'dot', ' ': 'spc', '_': 'shift-slash'}.get(c)
                if key is None:
                    raise RuntimeError('Unsupported character for Italian guest keyboard')
            command(folder, 'human-monitor-command', {'command-line': 'sendkey ' + key})
            time.sleep(.1)
        print('Typed in isolated guest')
    elif args.action == 'status':
        print(json.dumps(command(folder, 'query-status')))
    else:
        command(folder, 'quit')
        try:
            fd = os.pidfd_open(data['pid'])
        except ProcessLookupError:
            fd = None
        if fd is not None:
            try:
                if not select.select([fd], [], [], 25)[0]:
                    raise RuntimeError('Test VM has not finished closing; no process forced')
            finally:
                os.close(fd)
        print(json.dumps({'stopped_test_vm': data['pid']}))


if __name__ == '__main__':
    main()
