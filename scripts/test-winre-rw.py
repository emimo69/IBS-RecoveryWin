#!/usr/bin/env python3
"""Verify guest writes on a disposable 64 MiB file, never physical disks."""
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'.build/guest-test'

def main():
    pid=int((WORK/'pid').read_text())
    process=Path(f'/proc/{pid}')
    assert b'qemu-system-x86_64' in (process/'cmdline').read_bytes()
    # Refuse the test if this QEMU process holds ANY physical block device.
    for fd in (process/'fd').iterdir():
        try:
            assert not stat.S_ISBLK(fd.stat().st_mode),'Dispositivo fisico aperto: '+str(fd)
        except FileNotFoundError:
            pass
    fixture=WORK/'fixture.raw'
    assert fixture.stat().st_size==64*1024*1024
    with fixture.open('rb') as stream:assert stream.read(17)==b'IBS-TEST-FIXTURE\x00'
    script=ROOT/'scripts/test-winre-boot.py'
    def type_command(text):
        subprocess.run([sys.executable,str(script),'type',text],check=True)
        time.sleep(.3)
    # Create the DiskPart script in the guest RAM disk; does not depend on FAT caching.
    lines=['select disk 0','clean','create partition primary','format fs=ntfs quick label=IBSTEST','assign letter=T','exit']
    for i,line in enumerate(lines):
        type_command('echo '+line+(' > ' if i==0 else ' >> ')+r'x:\rwtest.txt')
    type_command(r'diskpart /s x:\rwtest.txt')
    deadline=time.monotonic()+120
    while time.monotonic()<deadline:
        data=fixture.read_bytes()
        if b'NTFS    ' in data:break
        time.sleep(.5)
    else:raise AssertionError('Formattazione NTFS del file disco non rilevata')
    # Wait for DiskPart to finish quick format before returning to cmd.
    time.sleep(5)
    marker='IBS-WINRE-RW-OK'
    type_command('echo '+marker+r' > t:\probe.txt')
    for _ in range(100):
        data=fixture.read_bytes()
        if marker.encode() in data:break
        time.sleep(.2)
    else:raise AssertionError('Scrittura file dal guest non rilevata nel disco virtuale')
    report={'result':'PASS','fixture':str(fixture),'bytes':len(data),'marker':marker,
            'operations':['DiskPart clean/create','NTFS quick format','guest file write'],
            'physical_disks_used':False}
    (WORK/'rw-result.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: WinRE vede, formatta NTFS e scrive sul disco virtuale passato RW a QEMU')

if __name__=='__main__':main()
