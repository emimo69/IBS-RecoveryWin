#!/usr/bin/env python3
"""Real XFCE terminal copy and paste on an isolated virtual X11 display."""
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import time
ROOT=Path(__file__).resolve().parents[1]

def main():
    display=subprocess.Popen(['Xvfb','-displayfd','1','-screen','0','1024x768x24','-nolisten','tcp'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
    number=display.stdout.readline().decode().strip()
    terminal=None;owner=None
    try:
        with tempfile.TemporaryDirectory(prefix='terminal-',dir=ROOT/'.build') as folder:
            work=Path(folder);config=work/'.config/xfce4/terminal';config.mkdir(parents=True)
            shutil.copyfile(ROOT/'config/includes.chroot/etc/skel/.config/xfce4/terminal/terminalrc',config/'terminalrc')
            env=dict(os.environ,DISPLAY=':'+number,HOME=folder,XDG_CONFIG_HOME=str(work/'.config'),LANG='C.UTF-8')
            probe=work/'probe.py';output=work/'input.txt'
            probe.write_text('from pathlib import Path\nimport time\ntext=input("INCOLLA: ")\nPath('+repr(str(output))+').write_text(text)\nprint("COPIA-OK",flush=True)\ntime.sleep(60)\n')
            terminal=subprocess.Popen(['dbus-run-session','--','xfce4-terminal','--disable-server','--title=IBS-Clipboard-Test','--execute','python3',str(probe)],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
            window=None
            for _ in range(100):
                result=subprocess.run(['xdotool','search','--name','IBS-Clipboard-Test'],env=env,capture_output=True,text=True)
                if result.returncode==0:
                    window=result.stdout.splitlines()[0];break
                time.sleep(.1)
            assert window,'Finestra terminale non trovata'
            time.sleep(.5)
            text='caffè € : \\ / | & > < "'
            owner=subprocess.Popen(['xclip','-selection','clipboard','-in','-quiet'],env=env,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            owner.stdin.write(text.encode());owner.stdin.close()
            subprocess.run(['xdotool','windowfocus','--sync',window],env=env,check=True)
            time.sleep(.2)
            subprocess.run(['xdotool','key','--clearmodifiers','ctrl+shift+v'],env=env,check=True)
            time.sleep(.3)
            subprocess.run(['xdotool','key','Return'],env=env,check=True)
            for _ in range(100):
                if output.exists():break
                time.sleep(.1)
            assert output.read_text()==text,output.read_text()
            subprocess.run(['xdotool','key','--clearmodifiers','ctrl+shift+a','ctrl+shift+c'],env=env,check=True)
            time.sleep(.2)
            copied=subprocess.check_output(['xclip','-selection','clipboard','-out'],env=env,timeout=3).decode()
            assert 'COPIA-OK' in copied and text in copied,repr(copied)
            print('PASS: Ctrl+Maiusc+V e Ctrl+Maiusc+C nel terminale XFCE reale, Unicode e simboli Windows')
    finally:
        if owner:
            if owner.poll() is None:owner.terminate()
            owner.wait(timeout=3)
        if terminal:
            os.killpg(terminal.pid,signal.SIGTERM)
            terminal.wait(timeout=5)
        display.terminate();display.wait(timeout=3)

if __name__=='__main__':main()
