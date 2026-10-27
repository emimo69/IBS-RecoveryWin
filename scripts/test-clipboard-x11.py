#!/usr/bin/env python3
"""Exercise the real X11 clipboard through the UNIX protocol used by WinRE."""
import os
from pathlib import Path
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'config/includes.chroot/usr/local/lib'))
from ibs2.clipboard import bridge, frame, Frames, READY, read_clipboard

def receive(conn):
    parser=Frames()
    while True:
        messages=parser.feed(conn.recv(65536))
        if messages:return messages[0]

def main():
    display=subprocess.Popen(['Xvfb','-displayfd','1','-screen','0','1024x768x24','-nolisten','tcp'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
    number=display.stdout.readline().decode().strip()
    if not number:raise RuntimeError('Xvfb non disponibile')
    os.environ['DISPLAY']=':'+number
    stop=threading.Event();owners=[];thread=None
    try:
        with tempfile.TemporaryDirectory(dir=ROOT/'.build',prefix='clip-') as folder:
            path=Path(folder)/'clipboard.sock'
            with socket.socket(socket.AF_UNIX) as server:
                server.bind(str(path));server.listen();server.settimeout(5)
                def set_host(text):
                    owner=subprocess.Popen(['xclip','-selection','clipboard','-in','-quiet'],stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                    owner.stdin.write(text.encode());owner.stdin.close();owners.append(owner)
                    for _ in range(50):
                        if read_clipboard()==text:return
                        time.sleep(.02)
                    raise AssertionError('X11 ownership')
                source='Debian -> WinRE: caffè € 文字\nseconda riga'
                set_host(source)
                thread=threading.Thread(target=bridge,args=(path,stop));thread.start()
                conn,_=server.accept()
                with conn:
                    conn.settimeout(5)
                    conn.sendall(struct.pack('<4sI',b'IBC2',READY))
                    assert receive(conn)==source
                    target='WinRE -> Debian: più righe\r\nàèìòù € 文字'
                    payload=frame(target)
                    for offset in range(0,len(payload),3):conn.sendall(payload[offset:offset+3])
                    for _ in range(100):
                        if read_clipboard()==target:break
                        time.sleep(.03)
                    assert read_clipboard()==target
                    set_host('Nuovo testo Debian')
                    assert receive(conn)=='Nuovo testo Debian'
                    set_host('')
                    assert receive(conn)==''
                print('PASS: appunti X11 reali bidirezionali, Unicode, multilinea e testo vuoto')
    finally:
        stop.set()
        if thread:thread.join(timeout=5)
        for owner in owners:
            if owner.poll() is None:owner.terminate()
            owner.wait(timeout=3)
        display.terminate();display.wait(timeout=3)

if __name__=='__main__':main()
