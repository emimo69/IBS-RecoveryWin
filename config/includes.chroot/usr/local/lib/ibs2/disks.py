"""Inventory and exclusive RW handoff of unmounted whole disks."""
import json
import os
from pathlib import Path
import re
import stat
import subprocess

MAX_DISKS = 5

def inventory():
    response = subprocess.run(['/usr/bin/lsblk', '--json', '--bytes', '--paths', '--output',
                             'PATH,KNAME,TYPE,SIZE,MODEL,SERIAL,RO,MOUNTPOINTS,LOG-SEC,PHY-SEC'],
                            check=True, capture_output=True, text=True)
    swap = set()
    with open('/proc/swaps') as stream:
        for line in list(stream)[1:]:
            swap.add(os.path.realpath(line.split()[0]))
    def descendants(node):
        yield node
        for child in node.get('children', []):
            yield from descendants(child)
    result = []
    for disk in json.loads(response.stdout)['blockdevices']:
        if disk['type'] != 'disk':
            continue
        reason = ''
        for node in descendants(disk):
            name = Path(node['kname']).name
            holders = Path('/sys/class/block') / name / 'holders'
            if node.get('ro'):
                reason = 'sola lettura'
            if any(node.get('mountpoints') or []):
                reason = 'montato o utilizzato dalla live'
            if os.path.realpath(node['path']) in swap:
                reason = 'swap attivo'
            if holders.exists() and any(holders.iterdir()):
                reason = 'in uso da RAID, LVM o altro dispositivo'
        disk['blocked'] = reason
        result.append(disk)
    return result

def open_disks(paths):
    if len(paths) > MAX_DISKS or len(set(paths)) != len(paths):
        raise ValueError('Selezionare al massimo cinque dischi distinti')
    current = {disk['path']: disk for disk in inventory()}
    opened = []
    try:
        for path in paths:
            if not re.fullmatch(r'/dev/[A-Za-z0-9_-]+', path):
                raise ValueError('Percorso disco non valido')
            disk = current.get(path)
            if not disk or disk['blocked']:
                raise ValueError(f'Disco non disponibile: {path}')
            before = os.stat(path, follow_symlinks=False)
            if not stat.S_ISBLK(before.st_mode):
                raise ValueError('È richiesto un disco fisico intero')
            # Kernel exclusive claim prevents concurrent mounting. Never unmount automatically.
            fd = os.open(path, os.O_RDWR | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_DIRECT)
            opened.append((fd, disk))
            probe = os.open(path, os.O_RDONLY | os.O_DIRECT | os.O_CLOEXEC | os.O_NOFOLLOW)
            disk['_probe_fd'] = probe
            if os.fstat(probe).st_rdev != before.st_rdev:
                raise ValueError('Identità disco cambiata durante apertura di verifica')
            if os.fstat(fd).st_rdev != before.st_rdev:
                raise ValueError('Identità del disco cambiata durante la selezione')
        # Recheck after exclusive claims, including mountpoints and dependent devices.
        latest = {disk['path']: disk for disk in inventory()}
        for _, disk in opened:
            entry = latest.get(disk['path'])
            if not entry or entry['blocked']:
                raise ValueError('Disco entrato in uso durante la selezione')
        return opened
    except BaseException:
        for fd, _ in opened:
            os.close(fd)
            if '_probe_fd' in _:
                os.close(_['_probe_fd'])
        raise
