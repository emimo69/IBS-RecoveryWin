"""Non-destructive regression tests: mocks replace OS/device boundaries only."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
IMAGE = ROOT / 'config/includes.chroot'
BIN = IMAGE / 'usr/local/bin'
SBIN = IMAGE / 'usr/local/sbin'
LIB = IMAGE / 'usr/local/lib/ibs-recoverywin'

MOCK = r'''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
cmd = Path(sys.argv[0]).name
args = sys.argv[1:]
with open(os.environ['CALLS'], 'a') as f:
    f.write(json.dumps([cmd, *args]) + '\n')
cfg = json.loads(os.environ.get('SCENARIO', '{}'))
if cmd == 'readlink': print(cfg.get('device', '/dev/sda'))
elif cmd == 'lsblk':
    col = args[args.index('-o')+1] if '-o' in args else args[-2]
    if 'PKNAME' in args: print('sdb')
    elif 'LABEL' in args: print('Ventoy')
    elif 'TRAN' in args and cfg.get('ventoy'): print('usb')
    elif args == ['-rnp', '-o', 'NAME,TYPE']: print('/dev/sdb1 part')
    else: print(cfg.get(col, {'TYPE':'disk','SIZE':'1000000','TRAN':'sata','RM':'0','RO':'0','NAME,TYPE':'/dev/sda disk\n/dev/sda1 part','FSTYPE':'ntfs','MOUNTPOINTS':''}.get(col,'')))
elif cmd in ('mkdir',): pass
elif cmd == 'mountpoint': sys.exit(1)
elif cmd == 'findmnt': sys.exit(1)
elif cmd == 'mount':
    sys.exit(0 if '/dev/loop42' in args and not cfg.get('loop_mount_fail') else 1)
elif cmd == 'losetup':
    if '--show' in args: print('/dev/loop42')
elif cmd == 'zenity':
    counter = Path(os.environ['COUNTER'])
    n = int(counter.read_text()) if counter.exists() else 0
    counter.write_text(str(n+1))
    responses = cfg.get('responses', [])
    if n < len(responses):
        response = responses[n]
        if response is None: sys.exit(1)
        if not any(x in args for x in ("--warning", "--info", "--error", "--question")):
            print(response)
elif cmd == 'pkexec':
    if cfg.get('pkexec_fail'): sys.exit(1)
    print(cfg.get('ventoy_path','/media/USB Ventoy'))
elif cmd == 'ibs-disk-check':
    if args[0] not in cfg.get('eligible', []): sys.exit(1)
    print(args[0])
elif cmd == 'qemu-system-x86_64': sys.exit(cfg.get('qemu_status', 0))
elif cmd == 'ibs-iso-select': print(cfg['iso'])
else:
    sys.exit('Unexpected mocked operation: '+cmd)
'''

class ScriptTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        self.mocks = self.directory / 'bin'
        self.mocks.mkdir()
        for cmd in ('readlink', 'lsblk', 'mkdir', 'mountpoint', 'findmnt', 'mount',
                    'losetup', 'zenity', 'pkexec', 'ibs-disk-check', 'qemu-system-x86_64', 'ibs-iso-select'):
            p = self.mocks / cmd
            p.write_text(MOCK)
            p.chmod(0o755)
        self.env = dict(os.environ, PATH=str(self.mocks)+os.pathsep+os.environ['PATH'],
                        CALLS=str(self.directory/'calls'), COUNTER=str(self.directory/'counter'))

    def run_script(self, path, args=(), scenario=None, source=None):
        self.env['SCENARIO'] = json.dumps(scenario or {})
        if source is not None:
            path = self.directory / 'script'
            path.write_text(source)
        return subprocess.run(['bash', str(path), *args], env=self.env, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def calls(self):
        return [json.loads(x) for x in (self.directory/'calls').read_text().splitlines()]

    def test_all_shell_syntax(self):
        files = [p for p in (ROOT/'config').rglob('*') if p.is_file() and
                 (p.read_bytes().startswith(b'#!/bin/') or p.suffix == '.sh')]
        self.assertGreater(len(files), 20)
        for p in files:
            with self.subTest(script=str(p.relative_to(ROOT))):
                result = subprocess.run(['bash', '-n', str(p)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_disk_policy(self):
        good = ['/dev/sda','/dev/nvme0n1','/dev/mmcblk0']
        bad = ['/dev/nbd0','/dev/loop0','/dev/dm-0','/dev/sda1','/dev/mmcblk0boot0','/dev/sr0']
        for name in good + bad:
            result = subprocess.run(['bash','-c', 'source "$1"; ibs_disk_metadata_allowed "$2" disk 1024 sata 0 0',
                                     'test', str(LIB/'disk-policy.sh'), name], capture_output=True)
            self.assertEqual(result.returncode == 0, name in good, name)

    def test_privileged_disk_validation(self):
        # The test copy simulates block-device existence and /sys holders.
        # All validation rules below that boundary are the production code.
        source = (SBIN/'ibs-disk-check').read_text().replace(
            '/usr/local/lib/ibs-recoverywin/disk-policy.sh', str(LIB/'disk-policy.sh'))
        source = source.replace('[[ -b "$DEV" ]]', 'true').replace('/sys/class/block/', str(self.directory/'sys')+'/')
        cases = [(True, {}), (False, {'device':'/dev/nbd0'}),
                 (False, {'SIZE':'0'}), (False, {'SIZE':'invalid'}),
                 (False, {'TRAN':'usb'}), (False, {'RM':'1'}), (False, {'RO':'1'}),
                 (False, {'TYPE':'part'}), (False, {'MOUNTPOINTS':'/run/live/medium'}),
                 (False, {'MOUNTPOINTS':'[SWAP]'}),
                 (False, {'NAME,TYPE':'/dev/sda disk\n/dev/dm-0 crypt'}),
                 (False, {'FSTYPE':'LVM2_member'}), (False, {'FSTYPE':'linux_raid_member'})]
        for expected, cfg in cases:
            with self.subTest(scenario=cfg):
                result = self.run_script(SBIN/'ibs-disk-check', ['/dev/sda'], cfg, source)
                self.assertEqual(result.returncode == 0, expected, result.stderr)
        holder = self.directory/'sys/sda1/holders/dm-0'
        holder.parent.mkdir(parents=True)
        holder.touch()
        self.assertNotEqual(self.run_script(SBIN/'ibs-disk-check', ['/dev/sda'], source=source).returncode, 0)

    def test_nonblock_device_rejected(self):
        file = self.directory/'plain-file'
        file.touch()
        source = (SBIN/'ibs-disk-check').read_text().replace(
            '/usr/local/lib/ibs-recoverywin/disk-policy.sh', str(LIB/'disk-policy.sh'))
        result = self.run_script(SBIN/'ibs-disk-check', [str(file)], {'device':str(file)}, source)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('blocchi', result.stderr)

    def test_ventoy_readonly_loop_fallback(self):
        result = self.run_script(SBIN/'ibs-ventoy-iso-mount', scenario={'ventoy':True})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, '/mnt/ibs-ventoy\n')
        calls = self.calls()
        self.assertIn(['losetup','--find','--show','--read-only','/dev/sdb1'], calls)
        self.assertIn(['mount','-o','ro,nosuid,nodev,noexec','/dev/loop42','/mnt/ibs-ventoy'], calls)
        self.assertFalse(any('/dev/mapper/ventoy' in x or x[0] in ('umount','dmsetup') for x in calls))

    def test_ventoy_failed_loop_detached(self):
        result = self.run_script(SBIN/'ibs-ventoy-iso-mount', scenario={'ventoy':True,'loop_mount_fail':True})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(['losetup','-d','/dev/loop42'], self.calls())

    def test_iso_path_has_real_newline(self):
        usb = self.directory/'USB Ventoy'
        usb.mkdir()
        iso = usb/'Windows RE.iso'
        iso.touch()
        result = self.run_script(BIN/'ibs-iso-select', scenario={
            'ventoy_path':str(usb), 'responses':['USB / Ventoy',str(iso)]})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, str(iso)+'\n')

    def test_no_nas_needed_when_ventoy_unavailable(self):
        result = self.run_script(BIN/'ibs-iso-select', scenario={
            'pkexec_fail':True,'responses':['USB / Ventoy','', '/tmp/local.iso']})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, '/tmp/local.iso\n')
        self.assertFalse(any('ibs-iso-nas-mount' in ' '.join(x) for x in self.calls()))

    def test_cancel_iso_selection(self):
        result = self.run_script(BIN/'ibs-iso-select', scenario={'responses':[None]})
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')

    def test_qemu_unprivileged_error(self):
        if os.geteuid() == 0:
            self.skipTest('This check requires an unprivileged test runner')
        for name in ('ibs-qemu-disk-session','ibs-qemu-disk-direct'):
            source = (SBIN/name).read_text().replace('/usr/local/lib/ibs-recoverywin/qemu-session.sh', str(LIB/'qemu-session.sh'))
            result = self.run_script(SBIN/name, ['/dev/sda'], source=source)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('pkexec', result.stderr)

    def test_shared_qemu_arguments(self):
        result = subprocess.run(['bash', '-c',
            'source "$1"; MODE=legacy; WORKDIR="$2"; ibs_qemu_args; printf "%s\\n" "${ARGS[@]}"',
            'test', str(LIB/'qemu-session.sh'), str(self.directory)],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        args = result.stdout.splitlines()
        self.assertIn('q35', args)
        self.assertIn('user,model=e1000', args)
        self.assertNotIn('-drive', args)  # legacy must not require or attach OVMF

    def test_revalidation_rejects_replaced_disk(self):
        source = (LIB/'qemu-session.sh').read_text().replace('/usr/local/sbin/ibs-disk-check', str(self.mocks/'ibs-disk-check'))
        source += '\nDISK=/dev/sda; IDENTITY=original; ibs_revalidate\n'
        result = self.run_script(LIB/'qemu-session.sh', source=source,
            scenario={'eligible':['/dev/sda'], 'MAJ:MIN,SIZE,MODEL,SERIAL,WWN':'replaced'})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("identità", result.stderr)

    def test_lock_serializes_both_modes(self):
        # Exercise the production session initializer with simulated root/OS boundaries.
        source = (LIB/'qemu-session.sh').read_text().replace('[[ $EUID == 0 ]]', 'true')
        source = source.replace('/usr/local/sbin/ibs-qemu-preflight', 'true')
        source = source.replace('/usr/local/sbin/ibs-disk-check', str(self.mocks/'ibs-disk-check'))
        source = source.replace('install -d -m 0700 -o root -g root /run/ibs-qemu', 'mkdir -p /run/ibs-qemu')
        source = source.replace('/run/ibs-qemu', str(self.directory/'locks'))
        auth = self.directory/'auth'
        auth.touch()
        self.env.update(DISPLAY=':test', XAUTHORITY=str(auth),
                        SCENARIO=json.dumps({'eligible':['/dev/sda'], 'MAJ:MIN':'8:0'}))
        # Use the real mkdir/flock for regular test files.
        (self.mocks/'mkdir').unlink()
        script = self.directory/'session'
        script.write_text(source+'\nDISK=/dev/sda; MODE=legacy; SESSION_KIND=$1; ibs_session_init; echo locked; read -r _\n')
        first = subprocess.Popen(['bash',str(script),'protected'], env=self.env,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            self.assertEqual(first.stdout.readline().strip(), 'locked')
            second = subprocess.run(['bash',str(script),'direct'], env=self.env,
                                    input='release\n', capture_output=True, text=True)
            self.assertNotEqual(second.returncode, 0)
            self.assertIn('già utilizzato', second.stderr)
        finally:
            first.communicate('release\n', timeout=5)
        third = subprocess.run(['bash',str(script),'direct'], env=self.env,
                               input='release\n', capture_output=True, text=True)
        self.assertEqual(third.returncode, 0, third.stderr)

    def test_iso_qemu_arguments_and_failure(self):
        (self.mocks/'mkdir').unlink()
        iso = self.directory/'Windows RE,original.iso'
        iso.write_text('original-image-fixture')
        self.env.update(HOME=str(self.directory), XDG_RUNTIME_DIR=str(self.directory),
                        XDG_STATE_HOME=str(self.directory/'state'))
        source = (BIN/'ibs-qemu-iso').read_text().replace('/usr/local/bin/ibs-iso-select', str(self.mocks/'ibs-iso-select'))
        result = self.run_script(BIN/'ibs-qemu-iso', source=source, scenario={
            'iso':str(iso), 'responses':['BIOS Legacy',''], 'qemu_status':3})
        self.assertEqual(result.returncode, 3, result.stderr)
        calls = self.calls()
        qemu = next(c for c in calls if c[0] == 'qemu-system-x86_64')
        self.assertIn('-no-reboot', qemu)
        self.assertEqual(qemu[qemu.index('-cdrom')+1], str(iso))
        self.assertEqual(iso.read_text(), 'original-image-fixture')
        self.assertFalse(list(self.directory.glob('ibs-qemu-iso.*')))
        logs = list((self.directory/'state/ibs-recoverywin').glob('*.log'))
        self.assertEqual(len(logs), 1)
        self.assertIn(str(iso), logs[0].read_text())

    def test_missing_graphical_session_fails_before_device_access(self):
        source = (LIB/'qemu-session.sh').read_text().replace('[[ $EUID == 0 ]]', 'true')
        source += '\nMODE=legacy; SESSION_KIND=direct; DISK=/dev/sda; unset DISPLAY XAUTHORITY; ibs_session_init\n'
        result = self.run_script(LIB/'qemu-session.sh', source=source)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('DISPLAY/XAUTHORITY', result.stderr)
        self.assertFalse((self.directory/'calls').exists())

    def test_policy_is_scoped_and_authenticated(self):
        policies = IMAGE/'usr/share/polkit-1/actions'
        for path in policies.glob('*.policy'):
            action = ET.parse(path).getroot().find('action')
            self.assertEqual(action.find('defaults/allow_any').text, 'no')
            self.assertEqual(action.find('defaults/allow_inactive').text, 'no')
            self.assertEqual(action.find('defaults/allow_active').text, 'auth_admin')
            annotations = {a.attrib['key']:a.text for a in action.findall('annotate')}
            self.assertTrue(annotations['org.freedesktop.policykit.exec.path'].startswith('/usr/local/sbin/ibs-'))
            self.assertEqual(annotations['org.freedesktop.policykit.exec.allow_gui'], 'true')

if __name__ == '__main__':
    unittest.main(verbosity=2)
