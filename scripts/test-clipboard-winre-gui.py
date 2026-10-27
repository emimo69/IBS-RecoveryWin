#!/usr/bin/env python3
"""Test console Ctrl+V and Ctrl+A/Ctrl+C in the existing file-only WinRE VM.
Run test-clipboard-winre.py first to start the helper clipboard component.
"""
import os,sys,subprocess,threading,time
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'config/includes.chroot/usr/local/lib'))
from ibs2.clipboard import bridge,read_clipboard
x=subprocess.Popen(['Xvfb','-displayfd','1','-screen','0','1024x768x24','-nolisten','tcp'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
os.environ['DISPLAY']=':'+x.stdout.readline().decode().strip()
stop=threading.Event();ready=threading.Event();owner=None;t=None
try:
 owner=subprocess.Popen(['xclip','-selection','clipboard','-in','-quiet'],stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 owner.stdin.write(b'echo IBS-PASTE-GUI-20261027');owner.stdin.close()
 t=threading.Thread(target=bridge,args=(root/'.build/guest-test/clipboard.sock',stop,ready));t.start()
 assert ready.wait(45),'handshake mancante'
 time.sleep(2)
 script=root/'scripts/test-winre-boot.py'
 subprocess.run([sys.executable,str(script),'key','esc','ctrl-v','ret'],check=True)
 time.sleep(3)
 subprocess.run([sys.executable,str(script),'screen'],check=True)
 (root/'.build/guest-test/paste-gui.png').write_bytes((root/'.build/guest-test/screen.png').read_bytes())
 subprocess.run([sys.executable,str(script),'key','ctrl-a','ctrl-c'],check=True)
 for _ in range(100):
  text=read_clipboard()
  if text and 'IBS-PASTE-GUI-20261027' in text and 'X:\\' in text:break
  time.sleep(.1)
 else:raise AssertionError('Copia da console non rilevata; controllare screenshot')
 print('PASS: Ctrl+V nel prompt WinRE e Ctrl+A/Ctrl+C verso X11, marcatore rilevato nel testo della console')
finally:
 stop.set()
 if t:t.join(timeout=5)
 if owner:
  owner.terminate();owner.wait(timeout=3)
 x.terminate();x.wait(timeout=3)
