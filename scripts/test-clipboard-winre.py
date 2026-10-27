#!/usr/bin/env python3
"""End-to-end Windows clipboard / private network / Linux X11 test in the running file-only VM."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'config/includes.chroot/usr/local/lib'))
from ibs2.clipboard import bridge,read_clipboard

def main():
    display=subprocess.Popen(['Xvfb','-displayfd','1','-screen','0','1024x768x24','-nolisten','tcp'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
    os.environ['DISPLAY']=':'+display.stdout.readline().decode().strip()
    stop=threading.Event();ready=threading.Event();thread=None;owner=None
    try:
        text='Debian -> WinRE: caffè € 文字\nseconda riga'
        owner=subprocess.Popen(['xclip','-selection','clipboard','-in','-quiet'],stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        owner.stdin.write(text.encode());owner.stdin.close()
        for _ in range(50):
            if read_clipboard()==text:break
            time.sleep(.03)
        thread=threading.Thread(target=bridge,args=(ROOT/'.build/guest-test/clipboard.sock',stop,ready))
        thread.start()
        script=ROOT/'scripts/test-winre-boot.py'
        subprocess.run([sys.executable,str(script),'key','esc'],check=True)
        subprocess.run([sys.executable,str(script),'type',r'c:\clip.exe --test'],check=True)
        if not ready.wait(45):raise RuntimeError('Nessuna handshake appunti dal componente WinRE')
        expected='WinRE -> Debian: caffè, €, 文字\r\nseconda riga'
        for _ in range(600):
            if read_clipboard()==expected:break
            time.sleep(.1)
        actual=read_clipboard()
        assert actual==expected,repr(actual)
        report={'result':'PASS','debian_to_windows':text,'windows_to_debian':actual,
                'transport':'QEMU guestfwd + local UNIX socket','windows_clipboard':'SetClipboardData/GetClipboardData CF_UNICODETEXT',
                'physical_disks_used':False}
        (ROOT/'.build/guest-test/clipboard-result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        print('PASS: testo Unicode e multilinea scambiato tra appunti Windows WinRE e X11 Debian')
    finally:
        stop.set()
        if thread:thread.join(timeout=5)
        if owner:
            if owner.poll() is None:owner.terminate()
            owner.wait(timeout=3)
        display.terminate();display.wait(timeout=3)

if __name__=='__main__':main()
