"""QEMU policy and launch. Disk graph uses read-only fdset backing by default."""
import fcntl
import json
import os
from pathlib import Path
import pwd
import re
import shutil
import stat
import subprocess
import tempfile
import time
from media import MediaError,MEDIA_ROOT,guest_guard,run,read_inventory,fingerprint,ventoy_disks,select_token,clean_path,ensure_media_root

OVMF_CODE=Path('/usr/share/OVMF/OVMF_CODE_4M.fd')
OVMF_VARS=Path('/usr/share/OVMF/OVMF_VARS_4M.fd')

def kvm_available():
    try:
        fd=os.open('/dev/kvm',os.O_RDWR|os.O_CLOEXEC)
        try:return fcntl.ioctl(fd,0xAE00,0)==12  # KVM_GET_API_VERSION, no VM created
        finally:os.close(fd)
    except OSError:return False

def disk_reasons(disk,rows,direct=False):
    family=[r for r in rows if r.get('_disk')==disk['name']]
    reasons=[]
    if disk.get('type')!='disk' or not int(disk.get('size') or 0):reasons.append('non è un disco intero valido')
    if disk['name'] in ventoy_disks(rows):reasons.append('disco Ventoy protetto')
    if any(r.get('mountpoints') for r in family):reasons.append('disco Live, montato o swap attivo')
    if any(r.get('type') not in ('disk','part') for r in family):reasons.append('volume attivo RAID/LVM/crypt')
    if direct and disk.get('ro'):reasons.append('disco hardware in sola lettura')
    return reasons

def disk_candidates(rows):
    return [r for r in rows if r.get('type')=='disk' and not disk_reasons(r,rows)]

def direct_phrase(disk):
    return 'SCRIVI '+disk['name']+' '+fingerprint(disk)[:8]

def qemu_args(*,kind,fd,firmware,kvm,code=None,variables=None,overlay=None,base_format='raw',base_driver='host_device',direct=False):
    if kind not in ('iso','disk') or firmware not in ('uefi','legacy'):
        raise MediaError('Tipo di avvio o firmware non valido.')
    if kind=='disk' and not kvm:
        raise MediaError('Avvio OS da disco richiede un host con KVM; TCG non è un collaudo Windows.')
    if kind=='disk' and not direct and not overlay:
        raise MediaError('Overlay obbligatorio per avvio protetto.')
    argv=['qemu-system-x86_64','-no-user-config','-name','IBS Recovery','-machine','q35',
          '-accel','kvm' if kvm else 'tcg','-cpu','host' if kvm else 'max',
          '-smp','2','-m','2048','-display','gtk','-vga','std','-nic','user,model=e1000e',
          '-device','ich9-ahci,id=ibs-ahci','-add-fd',f'fd={fd},set=1,opaque=ibs-base']
    if firmware=='uefi':
        if not code or not variables:raise MediaError('OVMF CODE/VARS mancanti.')
        argv+=['-drive','if=pflash,format=raw,unit=0,readonly=on,file='+str(code).replace(',',',,'),
               '-drive','if=pflash,format=raw,unit=1,file='+str(variables).replace(',',',,')]
    def block(value):argv.extend(['-blockdev',json.dumps(value,separators=(',',':'))])
    readonly=not direct or kind=='iso'
    block({'driver':base_driver,'filename':'/dev/fdset/1','node-name':'ibs-file','read-only':readonly,'auto-read-only':False})
    block({'driver':base_format,'file':'ibs-file','node-name':'ibs-base','read-only':readonly})
    if kind=='iso':
        argv+=['-device','ide-cd,drive=ibs-base,bus=ibs-ahci.0','-boot','order=d']
    else:
        drive='ibs-base'
        if not direct:
            block({'driver':'qcow2','file':{'driver':'file','filename':str(overlay)},'backing':'ibs-base','node-name':'ibs-disk'})
            drive='ibs-disk'
        argv+=['-device','ide-hd,drive='+drive+',bus=ibs-ahci.0','-boot','order=c']
    return argv

def ensure_live_medium():
    # Fail closed if the origin of a toram/removed boot medium is unknown.
    for target in ('/run/live/medium','/lib/live/mount/medium'):
        try:
            mounts=json.loads(run(['findmnt','--json','--mountpoint',target,'-o','MAJ:MIN']))['filesystems']
            if mounts and not str(mounts[0]['maj:min']).startswith('0:'):
                return
        except (MediaError,KeyError,ValueError):
            pass
    raise MediaError('Origine del supporto Live non verificabile: avvio da disco disabilitato per proteggerlo.')

def open_disk(token,direct=False,confirmation=''):
    # Never trust GUI names or stale inventory. O_EXCL additionally refuses busy
    # block devices and keeps a kernel claim for the lifetime of the passed fd.
    ensure_live_medium()
    rows=read_inventory();disk=select_token(rows,token,disk_candidates)
    reasons=disk_reasons(disk,rows,direct)
    if reasons:raise MediaError('; '.join(reasons))
    # La GUI ha già richiesto la modalità diretta e mostrato l'avviso; non imporre frasi.
    path=Path(disk['name']).resolve(strict=True)
    if str(path)!=disk['name'] or not stat.S_ISBLK(path.stat().st_mode):
        raise MediaError('Il supporto non è un dispositivo a blocchi canonico.')
    fd=os.open(path,(os.O_RDWR if direct else os.O_RDONLY)|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        actual=os.fstat(fd)
        if f'{os.major(actual.st_rdev)}:{os.minor(actual.st_rdev)}'!=disk['maj:min']:
            raise MediaError('Dispositivo cambiato durante la selezione.')
        fresh=read_inventory();again=select_token(fresh,token,disk_candidates)
        if disk_reasons(again,fresh,direct):raise MediaError('Disco ora in uso: avvio annullato.')
        # Refuse holders even if a mapper is not visible in the lsblk tree.
        for member in (r for r in fresh if r.get('_disk')==disk['name']):
            holders=Path('/sys/dev/block')/str(member.get('maj:min'))/'holders'
            if holders.exists() and any(holders.iterdir()):raise MediaError('Disco con volumi attivi: avvio annullato.')
        return fd,disk
    except BaseException:
        os.close(fd);raise

def launch(request):
    guest_guard()
    user=pwd.getpwnam('admin')
    firmware=request.get('firmware')
    kind=request.get('kind')
    kvm=kvm_available()
    fd=None
    if firmware not in ('uefi','legacy'):raise MediaError('Scegliere UEFI o Legacy.')
    if not shutil.which('qemu-system-x86_64') or not shutil.which('qemu-img'):raise MediaError('QEMU non installato.')
    if firmware=='uefi' and not (OVMF_CODE.is_file() and OVMF_VARS.is_file()):raise MediaError('OVMF UEFI non installato.')
    if kind=='disk' and not kvm:raise MediaError('KVM non esposto: avvio Windows da disco non disponibile in questa sessione.')
    display=request.get('display','')
    if not re.fullmatch(r':\d+(?:\.\d+)?',display):raise MediaError('Sessione grafica locale non disponibile.')
    available=int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')))
    if available<2560*1024:raise MediaError('Memoria insufficiente: servono almeno 2,5 GiB liberi per la VM da 2 GiB.')
    try:
        if kind=='iso':
            path=Path(clean_path(request.get('path','')))
            if path.suffix.lower()!='.iso' or not path.is_file() or not path.is_relative_to(MEDIA_ROOT):
                raise MediaError('ISO richiesta fuori dalla sorgente NAS/Ventoy selezionata.')
            if 'winre' in path.name.casefold() and not kvm:
                raise MediaError('WinRE richiede KVM/CPU host; il test Live TCG non prova WinRE annidato.')
            if not kvm and request.get('allow_tcg') is not True:
                raise MediaError('KVM non disponibile. Confermare TCG solo per ISO generiche non collaudate.')
            fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
            size=path.stat().st_size;direct=False;driver='file'
        elif kind=='disk':
            direct=request.get('direct') is True
            fd,disk=open_disk(request.get('token',''),direct,request.get('confirmation',''))
            size=int(disk['size']);driver='host_device'
        else:raise MediaError('Modalità di avvio non valida.')
        ensure_media_root()
        sessions=MEDIA_ROOT/'vms';sessions.mkdir(mode=0o755,parents=True,exist_ok=True)
        os.chmod(sessions,0o755)
        session=Path(tempfile.mkdtemp(prefix='vm-',dir=sessions));os.chown(session,user.pw_uid,user.pw_gid)
        variables=None
        if firmware=='uefi':
            variables=session/'OVMF_VARS.fd';shutil.copyfile(OVMF_VARS,variables);os.chown(variables,user.pw_uid,user.pw_gid)
        overlay=None
        if kind=='disk' and not direct:
            overlay=session/'session.qcow2'
            run(['qemu-img','create','-f','qcow2',str(overlay),str(size)])
            os.chown(overlay,user.pw_uid,user.pw_gid)
        argv=qemu_args(kind=kind,fd=fd,firmware=firmware,kvm=kvm,code=OVMF_CODE,variables=variables,
                       overlay=overlay,base_driver=driver,direct=direct)
        auth=request.get('xauthority',user.pw_dir+'/.Xauthority')
        env={'PATH':'/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin','HOME':user.pw_dir,
             'LANG':'it_IT.UTF-8','DISPLAY':display,'XAUTHORITY':auth,'XDG_RUNTIME_DIR':f'/run/user/{user.pw_uid}'}
        # QEMU runs as admin, never as root; only the validated open fd crosses.
        log=session/'qemu.log'
        with log.open('xb') as output:
            os.chown(log,user.pw_uid,user.pw_gid)
            proc=subprocess.Popen(argv,env=env,stdin=subprocess.DEVNULL,stdout=output,stderr=output,
                pass_fds=(fd,),user=user.pw_uid,group=user.pw_gid,extra_groups=os.getgrouplist('admin',user.pw_gid),start_new_session=True)
        time.sleep(2)
        if proc.poll() is not None:raise MediaError('QEMU non avviato. Log locale: '+str(log))
        return {'pid':proc.pid,'session':str(session),'protected':not direct,'firmware':firmware}
    finally:
        if fd is not None:os.close(fd)
