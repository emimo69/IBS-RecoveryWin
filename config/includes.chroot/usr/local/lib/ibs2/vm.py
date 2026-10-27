"""QEMU UEFI runtime; disks arrive as pre-opened exclusive file descriptors."""
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import threading
from .clipboard import bridge

ISO = Path('/opt/ibs/iso/IBS-WinRE.iso')
CODE = Path('/usr/share/OVMF/OVMF_CODE_4M.fd')
VARS = Path('/usr/share/OVMF/OVMF_VARS_4M.fd')

def command(runtime, disks, *, iso=ISO, display='gtk', memory=2048, acceleration=None):
    accel = acceleration or ('kvm' if os.access('/dev/kvm', os.R_OK | os.W_OK) else 'tcg')
    args = ['/usr/bin/qemu-system-x86_64', '-name', 'IBS-WinRE', '-machine', f'q35,accel={accel}',
            '-cpu', 'host' if accel == 'kvm' else 'max', '-m', str(memory), '-smp', '2',
            '-drive', f'if=pflash,format=raw,readonly=on,file={CODE}',
            '-drive', f'if=pflash,format=raw,file={runtime / "OVMF_VARS.fd"}',
            '-drive', f'file={iso},media=cdrom,readonly=on,format=raw,if=ide,index=0',
            '-boot', 'order=d', '-display', display, '-nic',
            'user,model=e1000e,guestfwd=tcp:10.0.2.100:17625-chardev:clip',
            '-chardev', f'socket,id=clip,path={runtime / "clipboard.sock"},server=on,wait=off',
            '-serial', 'none', '-device', 'qemu-xhci', '-device', 'usb-tablet']
    for i, (fd, disk) in enumerate(disks):
        serial = re.sub(r'[^A-Za-z0-9_-]', '_', str(disk.get('serial') or f'IBS_DISK_{i}'))[:20]
        logical = int(disk.get('log-sec') or 512)
        physical = int(disk.get('phy-sec') or logical)
        if logical not in (512, 4096) or physical not in (512, 4096):
            raise ValueError('Dimensione settore disco non supportata')
        args += ['-add-fd', f'fd={fd},set={i + 1}',
                 '-add-fd', f'fd={disk["_probe_fd"]},set={i + 1}', '-drive',
                 f'file=/dev/fdset/{i + 1},format=raw,if=none,id=physical{i},cache=none,file.locking=off',
                 '-device', f'ide-hd,drive=physical{i},bus=ide.{i + 1},serial={serial},logical_block_size={logical},physical_block_size={physical}']
    return args

def launch(disks):
    if not ISO.is_file():
        raise RuntimeError('ISO WinRE assente')
    runtime_root = Path(f'/run/user/{os.getuid()}')
    if not runtime_root.is_dir() or runtime_root.stat().st_uid != os.getuid():
        raise RuntimeError('Sessione desktop admin non disponibile')
    with tempfile.TemporaryDirectory(prefix='ibs-winre-', dir=runtime_root) as folder:
        runtime = Path(folder)
        shutil.copyfile(VARS, runtime / 'OVMF_VARS.fd')
        stop = threading.Event()
        child = subprocess.Popen(command(runtime, disks), pass_fds=[item for fd, disk in disks for item in (fd, disk['_probe_fd'])])
        thread = threading.Thread(target=bridge, args=(runtime / 'clipboard.sock', stop), daemon=True)
        thread.start()
        try:
            return child.wait()
        finally:
            if child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    child.kill(); child.wait()
            stop.set()
            thread.join(timeout=5)
