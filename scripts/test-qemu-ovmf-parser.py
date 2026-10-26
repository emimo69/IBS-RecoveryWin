#!/usr/bin/env python3
"""Real QEMU pflash parser checks on disposable files; no guest execution."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'config/includes.chroot/usr/local/lib/ibs-recovery'))
import vm


class ParserTests(unittest.TestCase):
    def test_real_pflash_paths_and_readonly(self):
        qemu = shutil.which('qemu-system-x86_64')
        self.assertIsNotNone(qemu, 'QEMU required: no mock fallback')
        print(subprocess.run([qemu, '--version'], check=True, capture_output=True,
                             text=True, timeout=5).stdout.splitlines()[0], flush=True)
        for suffix in (' con spazi', ',uno,,due con spazi,è'):
            with self.subTest(suffix=suffix), tempfile.TemporaryDirectory(
                    dir=ROOT, prefix='.r4d-parser-') as tmp:
                folder = Path(tmp) / ('OVMF' + suffix)
                folder.mkdir()
                code, variables = [folder / (name + suffix + '.fd') for name in ('CODE', 'VARS')]
                for path in (code, variables):
                    with path.open('xb') as stream:
                        stream.truncate(4 * 1024 * 1024)
                before = [hashlib.sha256(p.read_bytes()).hexdigest() for p in (code, variables)]
                args = vm.qemu_args(kind='iso', fd=4, firmware='uefi', kvm=False,
                                    code=code, variables=variables)
                # Exercise the exact production -drive values, without ISO/fdset/network/GUI.
                drives = [args[i + 1] for i, arg in enumerate(args) if arg == '-drive']
                command = [qemu, '-no-user-config', '-nodefaults', '-machine', 'q35',
                           '-accel', 'tcg', '-m', '64', '-S', '-display', 'none',
                           '-nic', 'none', '-monitor', 'none', '-serial', 'none',
                           '-qmp', 'stdio']
                for drive in drives:
                    command.extend(['-drive', drive])
                requests = [dict(execute=name, id=name) for name in
                            ('qmp_capabilities', 'query-status', 'query-block', 'quit')]
                # run() kills and reaps QEMU on timeout; context then removes fixtures.
                result = subprocess.run(command, input=''.join(json.dumps(r) + '\n' for r in requests),
                                        capture_output=True, text=True, timeout=15)
                self.assertEqual(result.returncode, 0, result.stderr)
                replies = {r['id']: r for line in result.stdout.splitlines()
                           if 'id' in (r := json.loads(line))}
                for request in requests:
                    self.assertIn('return', replies[request['id']], result.stdout)
                self.assertFalse(replies['query-status']['return']['running'])
                inserted = [b['inserted'] for b in replies['query-block']['return']]
                self.assertEqual(len(inserted), 2)
                by_path = {b['file']: b for b in inserted}
                self.assertTrue(by_path[str(code)]['ro'])
                self.assertFalse(by_path[str(variables)]['ro'])
                self.assertEqual(before, [hashlib.sha256(p.read_bytes()).hexdigest()
                                          for p in (code, variables)])
                print('PASS: exact QMP filenames, CODE ro, VARS rw, CPU stopped, files unchanged: '
                      + suffix, flush=True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
