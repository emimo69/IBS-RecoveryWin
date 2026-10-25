#!/usr/bin/env python3
"""Real qemu-img/qemu-io checks on mock files only. No VM or physical disk."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import tempfile
root=Path('/opt/ibs-recoverywin-1.0')
for tool in ('qemu-img','qemu-io'):
    if not shutil.which(tool):raise SystemExit('Manca '+tool+'; nessun pacchetto installato automaticamente.')
work=Path(tempfile.mkdtemp(prefix='qcow2-fixture-',dir=root/'.build'))
base=work/'OS fittizio, senza Windows.qcow2'
overlay=work/'Overlay con spazi,è.qcow2'
def run(args):
    return subprocess.run(args,check=True,capture_output=True,text=True,timeout=30).stdout
run(['qemu-img','create','-f','qcow2',str(base),'64M'])
run(['qemu-io','-f','qcow2','-c','write -P 0x11 0 4096',str(base)])
original=hashlib.sha256(base.read_bytes()).hexdigest()
run(['qemu-img','create','-f','qcow2',str(overlay),'64M'])
graph={'driver':'qcow2','file':{'driver':'file','filename':str(overlay)},
       'backing':{'driver':'qcow2','read-only':True,'file':{'driver':'file','filename':str(base),'read-only':True}}}
run(['qemu-io','-c','read -P 0x11 0 4096','-c','write -P 0x22 0 4096','json:'+json.dumps(graph)])
run(['qemu-io','-c','read -P 0x22 0 4096','json:'+json.dumps(graph)])
run(['qemu-io','-r','-f','qcow2','-c','read -P 0x11 0 4096',str(base)])
assert hashlib.sha256(base.read_bytes()).hexdigest()==original
run(['qemu-img','check',str(base)]);run(['qemu-img','check',str(overlay)])
result={'mock_only':True,'base_unchanged':True,'base_sha256':original,'overlay_write_and_read':True,'paths_with_spaces_commas_unicode':True,'no_vm_started':True}
(work/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print('OK: QCOW2 fittizio, backing RO, scrittura solo overlay, base invariata, check formati; nessuna VM.')
print('Fixture locali: '+str(work.relative_to(root)))
