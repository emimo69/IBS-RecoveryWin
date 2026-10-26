#!/usr/bin/env python3
"""Read-only R6 gate. Success is structural validation, never boot authorization."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import struct
import subprocess


class Unsafe(ValueError):
    pass


def local_file(value):
    p = Path(value)
    if not p.is_absolute() or '..' in p.parts:
        raise Unsafe('Serve un percorso assoluto senza ..: ' + str(p))
    if p.parts[1:2] in [('dev',), ('proc',), ('sys',), ('media',), ('mnt',)]:
        raise Unsafe('Percorso dispositivo/remoto/rimovibile vietato: ' + str(p))
    if str(p).startswith('/run/media/'):
        raise Unsafe('Supporto rimovibile vietato')
    for part in [*reversed(p.parents), p]:
        if part.is_symlink():
            raise Unsafe('Symlink vietato: ' + str(part))
    if not stat.S_ISREG(p.stat().st_mode):
        raise Unsafe('Serve un file regolare: ' + str(p))
    # Fail closed on unknown/network filesystems, including bind-mounted USB.
    mounts = []
    for line in Path('/proc/self/mountinfo').read_text().splitlines():
        left, right = line.split(' - ', 1)
        fields = left.split()
        mount = re.sub(r'\\([0-7]{3})', lambda m: chr(int(m[1], 8)), fields[4])
        if p == Path(mount) or Path(mount) in p.parents:
            mounts.append((len(mount), fields[2], right.split()[0]))
    if not mounts:
        raise Unsafe('Mount non determinabile')
    _, device, fs = max(mounts)
    if fs not in {'ext2', 'ext3', 'ext4', 'xfs', 'btrfs', 'overlay', 'tmpfs'}:
        raise Unsafe('Filesystem non autorizzato: ' + fs)
    sysdev = Path('/sys/dev/block') / device
    if sysdev.exists():
        target = sysdev.resolve()
        if (target / 'slaves').is_dir() and any((target / 'slaves').iterdir()):
            raise Unsafe('Device composto: provenienza USB non verificabile')
        if 'usb' in str(target).lower():
            raise Unsafe('Mount su USB vietato')
        for parent in [target, *target.parents]:
            flag = parent / 'removable'
            if flag.is_file() and flag.read_text().strip() == '1':
                raise Unsafe('Mount rimovibile vietato')
    return p


def digest(p):
    h = hashlib.sha256()
    with p.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def qcow(p, backing=None):
    with p.open('rb') as f:
        header = f.read(104)
        if len(header) < 72 or header[:4] != b'QFI\xfb':
            raise Unsafe('Header QCOW2 mancante: ' + str(p))
        version, offset, length = struct.unpack('>IQI', header[4:20])
        if int.from_bytes(header[32:36], 'big'):
            raise Unsafe('QCOW2 cifrata non autorizzata')
        if version not in (2, 3):
            raise Unsafe('Versione QCOW2 inattesa')
        if version == 3 and (len(header) < 104 or int.from_bytes(header[72:80], 'big')):
            raise Unsafe('Feature incompatibili QCOW2 (dirty/corrupt/external data incluse)')
        if bool(offset) != bool(length) or length > 4096 or offset + length > p.stat().st_size:
            raise Unsafe('Riferimento backing incoerente')
        f.seek(offset)
        name = f.read(length).decode('utf-8') if length else None
    if name != (str(backing) if backing else None):
        raise Unsafe('Catena QCOW2 inattesa: ' + str(p))
    # No backing traversal: validate this image with an explicit null backing.
    graph = {'driver': 'qcow2', 'file': {'driver': 'file', 'filename': str(p)}, 'backing': None}
    args = ['qemu-img', 'check', '--output=json', 'json:' + json.dumps(graph)]
    result = subprocess.run(args, capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise Unsafe('QCOW2 non integra: ' + result.stderr.strip())
    report = json.loads(result.stdout)
    if report.get('corruptions', 0) or report.get('check-errors', 0) or report.get('leaks', 0):
        raise Unsafe('QCOW2 con errori o cluster persi')
    result = subprocess.run(['qemu-img', 'info', '--output=json', 'json:' + json.dumps(graph)],
                            capture_output=True, text=True, timeout=30, check=True)
    info = json.loads(result.stdout)
    if info.get('format') != 'qcow2' or info.get('virtual-size', 0) <= 0:
        raise Unsafe('Formato/dimensione virtuale QCOW2 incoerente')
    return info['virtual-size']


def validate(args):
    paths = [local_file(getattr(args, key)) for key in ('iso', 'code', 'vars', 'base', 'overlay')]
    iso, code, variables, base, overlay = paths
    if len({(p.stat().st_dev, p.stat().st_ino) for p in paths}) != 5:
        raise Unsafe('Ruoli duplicati o hardlink fra input')
    if not re.fullmatch('[0-9a-fA-F]{64}', args.iso_sha256) or digest(iso) != args.iso_sha256.lower():
        raise Unsafe('SHA-256 ISO diverso da quello atteso')
    with iso.open('rb') as f:
        f.seek(32768)
        if f.read(7) != b'\x01CD001\x01':
            raise Unsafe('Descrittore ISO9660 primario mancante')
    if (code.stat().st_size, variables.stat().st_size) not in {(3653632, 540672), (1966080, 131072)}:
        raise Unsafe('Dimensioni coppia OVMF non compatibili (2M/4M)')
    for p in (code, variables):
        with p.open('rb') as f:
            f.seek(40)
            if f.read(4) != b'_FVH':
                raise Unsafe('Firma firmware volume OVMF mancante: ' + str(p))
    if qcow(base) != qcow(overlay, base):
        raise Unsafe('Dimensioni virtuali base/overlay diverse')
    return {'status': 'prerequisiti strutturali verificati; boot NON autorizzato',
            'files': {str(p): {'bytes': p.stat().st_size, 'sha256': digest(p)} for p in paths},
            'kvm_accessible': os.access('/dev/kvm', os.R_OK | os.W_OK),
            'free_bytes': os.statvfs(overlay.parent).f_bavail * os.statvfs(overlay.parent).f_frsize}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('iso', 'code', 'vars', 'base', 'overlay', 'iso-sha256'):
        parser.add_argument('--' + key, required=True)
    try:
        print(json.dumps(validate(parser.parse_args()), indent=2))
        return 0
    except (Unsafe, OSError, ValueError, subprocess.SubprocessError) as exc:
        print('Preflight R6 fallito: ' + str(exc))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
