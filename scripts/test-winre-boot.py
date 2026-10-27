#!/usr/bin/env python3
"""Boot existing NAS WinRE with only a disposable file disk and FAT helper directory.
Does not build any ISO and never passes through physical disks.
"""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
import struct
import zlib

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / 'config/includes.chroot/usr/local/lib'
sys.path.insert(0, str(LIB))
from ibs2.vm import command
WORK = ROOT / '.build/guest-test'
WORK.mkdir(parents=True, exist_ok=True)

def request(name, arguments=None):
    with socket.socket(socket.AF_UNIX) as conn:
        conn.settimeout(15)
        conn.connect(str(WORK / 'qmp.sock'))
        stream = conn.makefile('rwb', buffering=0)
        stream.readline()
        for cmd in [{'execute':'qmp_capabilities'}, {'execute':name, 'arguments':arguments or {}}]:
            stream.write(json.dumps(cmd).encode()+b'\n')
            while True:
                result = json.loads(stream.readline())
                if 'return' in result or 'error' in result:
                    break
        if 'error' in result:
            raise RuntimeError(result)
        output = result['return']
        if name == 'human-monitor-command' and isinstance(output, str) and output.startswith('invalid parameter:'):
            raise ValueError(output)
        return output

def start():
    if (WORK/'pid').exists():
        old_pid=int((WORK/'pid').read_text())
        if Path(f'/proc/{old_pid}').exists():
            raise SystemExit('Test già avviato; arrestarlo prima di ricominciare')
        (WORK/'pid').unlink()
    (WORK/'qmp.sock').unlink(missing_ok=True)
    (WORK/'clipboard.sock').unlink(missing_ok=True)
    helper = WORK / 'helper'; helper.mkdir(exist_ok=True)
    shutil.copyfile(ROOT/'assets/ibs-clipboard.exe', helper/'clip.exe')
    (helper/'rwtest.txt').write_bytes(b'select disk 0\r\nonline disk\r\nattributes disk clear readonly\r\nclean\r\ncreate partition primary\r\nformat fs=ntfs quick label=IBSTEST\r\nassign letter=T\r\nexit\r\n')
    fixture = WORK/'fixture.raw'
    with fixture.open('wb') as stream:
        stream.truncate(64*1024*1024)
        stream.write(b'IBS-TEST-FIXTURE\x00')
    shutil.copyfile('/usr/share/OVMF/OVMF_VARS_4M.fd', WORK/'OVMF_VARS.fd')
    fd = os.open(fixture, os.O_RDWR | os.O_DIRECT)
    probe = os.open(fixture, os.O_RDONLY | os.O_DIRECT)
    args = command(WORK, [(fd, {'serial':'IBS_TEST_ONLY', '_probe_fd':probe})],
                   iso=ROOT/'config/includes.chroot/opt/ibs/iso/IBS-WinRE.iso', display='none', acceleration='tcg')
    args += ['-drive', f'file=fat:rw:{helper},if=ide,index=2,format=raw',
             '-qmp', f'unix:{WORK / "qmp.sock"},server=on,wait=off']
    with (WORK/'qemu.log').open('wb') as log:
        child = subprocess.Popen(args, pass_fds=[fd,probe], stdout=log, stderr=log, start_new_session=True)
    os.close(fd)
    os.close(probe)
    (WORK/'pid').write_text(str(child.pid))
    for _ in range(100):
        if (WORK/'qmp.sock').exists():
            break
        if child.poll() is not None:
            raise RuntimeError((WORK/'qemu.log').read_text())
        time.sleep(.1)
    # Boot optical media promptly when OVMF requests any key.
    for _ in range(5):
        if child.poll() is not None:
            raise RuntimeError((WORK/'qemu.log').read_text())
        time.sleep(1)
        request('human-monitor-command', {'command-line':'sendkey ret'})
    print('WinRE test avviata, pid', child.pid)

def main():
    action = sys.argv[1]
    if action == 'start':
        start()
    elif action == 'screen':
        request('screendump', {'filename': str(WORK/'screen.ppm')})
        ppm = WORK/'screen.ppm'
        with ppm.open('rb') as stream:
            assert stream.readline().strip()==b'P6'
            width,height=map(int,stream.readline().split())
            assert stream.readline().strip()==b'255'
            raw=stream.read()
        def chunk(kind,data):
            return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data))
        rows=b''.join(b'\0'+raw[i*width*3:(i+1)*width*3] for i in range(height))
        png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b'')
        (WORK/'screen.png').write_bytes(png)
        print(WORK/'screen.png')
    elif action == 'key':
        for key in sys.argv[2:]:
            request('human-monitor-command', {'command-line':'sendkey '+key})
            time.sleep(.08)
    elif action == 'type':
        text=sys.argv[2]
        punctuation={' ':'spc',':':'shift-dot','\\':'grave_accent','-':'slash','.':'dot','/':'shift-7','"':'shift-2','>':'shift-less','|':'shift-grave_accent','_':'shift-slash','=':'shift-0'}
        for char in text:
            key='grave_accent' if ord(char)==92 else punctuation.get(char)
            if key is None:
                if char.isascii() and char.isalnum():
                    key=('shift-' if char.isupper() else '')+char.lower()
                else:
                    raise ValueError('Carattere non gestito dal layout italiano: '+repr(char))
            request('human-monitor-command',{'command-line':'sendkey '+key})
            time.sleep(.12)
        request('human-monitor-command',{'command-line':'sendkey ret'})
    elif action == 'stop':
        pid=int((WORK/'pid').read_text())
        request('quit')
        for _ in range(100):
            if not Path(f'/proc/{pid}').exists():
                break
            time.sleep(.1)
        else:
            raise RuntimeError('La VM non è terminata')
        (WORK/'pid').unlink()
    else:
        raise SystemExit('start | screen | key KEY... | stop')

if __name__ == '__main__':
    main()
