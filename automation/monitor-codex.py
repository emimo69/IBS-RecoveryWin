#!/usr/bin/env python3
"""Monitor di sola lettura per Codex unattended. Non mostra credenziali o trascrizioni."""
import json
from pathlib import Path
import subprocess
import time
from datetime import datetime

ROOT=Path('/opt/ibs-recoverywin-1.0')
STATE=ROOT/'.task-watch'

def read(name):
    try:
        return json.loads((STATE/name).read_text())
    except (OSError, ValueError):
        return {}

def date(t):
    if not isinstance(t,(int,float)):
        return '-'
    return datetime.fromtimestamp(t).strftime('%d/%m/%Y %H:%M:%S')

def git(*args):
    try:
        return subprocess.run(['git','-C',str(ROOT),*args],capture_output=True,text=True,timeout=4).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return '-'

status=read('runner-status.json')
task=status.get('task','')
record=read('runs/'+task+'.json') if task else {}
print('=== IBS-RecoveryWin | Monitor Codex automatico ===')
print('Ora:',date(time.time()))
print('Timer: ',end='')
try:
    p=subprocess.run(['systemctl','--user','is-active','ibs-task-watch.timer'],capture_output=True,text=True,timeout=4)
    print(p.stdout.strip() or 'non disponibile')
except (OSError,subprocess.TimeoutExpired):
    print('non disponibile')
print('Runner:', 'abilitato' if (STATE/'unattended-enabled').exists() else 'solo controllo GitHub')
print('Stato:',status.get('status','non disponibile'))
print('Ultimo controllo:',date(status.get('timestamp')))
print('Task (hash):',task[:12] if task else '-')
print('Inizio lavoro:',date(record.get('started')))
if record.get('status')=='running':
    print('Tempo trascorso:',int(max(0,time.time()-record.get('started',time.time()))//60),'min')
print('Esito:',record.get('status',status.get('status','-')))
print('Errore/categoria:',record.get('reason',status.get('reason','-')))
print('Codice uscita:',record.get('exit_code','-'))
print('Ultimo commit:',git('log','-1','--format=%h %s'))
print('Modifiche locali:',git('status','--porcelain') or 'nessuna')
print('')
print('Aggiornamento automatico dello schermo: Ctrl+C per uscire dal monitor.')
