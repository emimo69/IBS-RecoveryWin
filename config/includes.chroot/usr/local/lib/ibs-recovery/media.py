"""IBS media policy. Pure inventory/validation separate from guest-only actions."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

MEDIA_ROOT=Path('/run/ibs-media')
class MediaError(RuntimeError):
    pass

def run(argv, **kwargs):
    result=subprocess.run(argv,capture_output=True,text=True,timeout=60,**kwargs)
    if result.returncode:
        raise MediaError(f'Comando {Path(argv[0]).name} fallito (codice {result.returncode}).')
    return result.stdout

def guest_guard():
    flags=Path('/proc/cmdline').read_text().split()
    if os.geteuid()!=0 or 'boot=live' not in flags or 'hostname=ibs-recoverywin' not in flags:
        raise MediaError('Operazione permessa solo nella Live IBS come amministratore, non sul server di sviluppo.')

def inventory(data):
    result=[]
    def visit(node,parent=None,disk=None):
        if node.get('type')=='disk':
            disk=node
        row={k:v for k,v in node.items() if k!='children'}
        row['_disk']=disk.get('name') if disk else None
        row['_transport']=disk.get('tran') if disk else None
        row['_serial']=disk.get('serial') if disk else None
        row['_parent']=parent.get('name') if parent else None
        row['mountpoints']=[m for m in row.get('mountpoints',[]) or [] if m]
        result.append(row)
        for child in node.get('children',[]):
            visit(child,node,disk)
    for node in data.get('blockdevices',[]):
        visit(node)
    return result

def read_inventory():
    return inventory(json.loads(run(['lsblk','--json','--paths','--bytes','--output',
        'NAME,TYPE,LABEL,FSTYPE,TRAN,PKNAME,MOUNTPOINTS,RO,SIZE,MODEL,SERIAL,MAJ:MIN'])))

def fingerprint(row):
    fields=('name','type','size','maj:min','serial','label','_serial','_disk')
    return hashlib.sha256(json.dumps({k:row.get(k) for k in fields},sort_keys=True).encode()).hexdigest()

def ventoy_disks(rows):
    return {r['_disk'] for r in rows if str(r.get('label') or '').casefold() in ('ventoy','vtoyefi')}

def ventoy_candidates(rows):
    known=ventoy_disks(rows)
    return [r for r in rows if r.get('type')=='part' and r.get('_transport')=='usb'
            and (str(r.get('label') or '').casefold()=='ventoy' or
                 (r['_disk'] in known and re.search(r'(\d+)$',r['name']) and re.search(r'(\d+)$',r['name']).group(1)=='1'))
            and str(r.get('label') or '').casefold()!='vtoyefi']

def select_token(rows,token,candidates):
    matches=[r for r in candidates(rows) if fingerprint(r)==token]
    if len(matches)!=1:
        raise MediaError('Supporto cambiato o non valido: aggiornare la selezione.')
    return matches[0]

def clean_path(value):
    if not value or any(ord(c)<32 for c in value):
        raise MediaError('Percorso vuoto o contenente caratteri di controllo.')
    return str(Path(value).resolve(strict=True))

def mount_nas():
    guest_guard()
    MEDIA_ROOT.mkdir(mode=0o755,exist_ok=True)
    target=MEDIA_ROOT/'qnap'
    target.mkdir(mode=0o755,exist_ok=True)
    if not os.path.ismount(target):
        # Guest authentication, no password/token/config credential files.
        run(['mount','-t','cifs','//192.168.20.123/Public',str(target),'-o',
             'guest,ro,nosuid,nodev,noexec,vers=3.0,prefixpath=ISO'])
    # Never reuse an unexpected or writable mount at our fixed location.
    info=json.loads(run(['findmnt','--json','--mountpoint',str(target),'-o','SOURCE,FSTYPE,OPTIONS']))['filesystems'][0]
    if info['fstype']!='cifs' or info['source'] not in ('//192.168.20.123/Public','//192.168.20.123/Public/ISO') or 'ro' not in info['options'].split(','):
        raise MediaError('Il punto NAS esistente non corrisponde alla sorgente guest in sola lettura.')
    return clean_path(str(target))

def mount_ventoy(token):
    guest_guard()
    part=select_token(read_inventory(),token,ventoy_candidates)
    MEDIA_ROOT.mkdir(mode=0o755,exist_ok=True)
    target=MEDIA_ROOT/('ventoy-'+token[:16])
    target.mkdir(mode=0o755,exist_ok=True)
    if os.path.ismount(target):
        info=json.loads(run(['findmnt','--json','--mountpoint',str(target),'-o','MAJ:MIN,OPTIONS']))['filesystems'][0]
        if info['maj:min']!=part['maj:min'] or 'ro' not in info['options'].split(','):
            raise MediaError('Vista Ventoy esistente non valida o non in sola lettura.')
        return clean_path(str(target))
    existing=part['mountpoints']
    if existing:
        origin=clean_path(existing[0])
        run(['mount','--bind',origin,str(target)])
        try:
            run(['mount','-o','remount,bind,ro,nosuid,nodev,noexec',str(target)])
        except MediaError:
            run(['umount',str(target)])
            raise
    else:
        fstype=str(part.get('fstype') or '').lower()
        if fstype not in ('exfat','vfat','ntfs','ntfs3'):
            raise MediaError('Ventoy: filesystem non supportato per montaggio sicuro (attesi exFAT, FAT o NTFS).')
        options='ro,nosuid,nodev,noexec'
        driver=fstype
        if fstype in ('ntfs','ntfs3'):
            driver='ntfs-3g';options+=',norecover'
        run(['mount','-t',driver,'-o',options,part['name'],str(target)])
    info=json.loads(run(['findmnt','--json','--mountpoint',str(target),'-o','MAJ:MIN,OPTIONS']))['filesystems'][0]
    if info['maj:min']!=part['maj:min'] or 'ro' not in info['options'].split(','):
        raise MediaError('Vista Ventoy non verificata in sola lettura: selezione interrotta.')
    return clean_path(str(target))
