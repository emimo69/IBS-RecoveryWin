#!/usr/bin/env python3
"""R4 fixture/mock checks: no mounts, devices, network or QEMU processes."""
import ast
from contextlib import ExitStack
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'config/includes.chroot/usr/local/lib/ibs-recovery'))
import media
import vm


class PathTests(unittest.TestCase):
    def test_iso_selection_nas_and_ventoy(self):
        # Load GUI definitions only; never execute its top-level run_vm().
        source = ROOT / 'config/includes.chroot/usr/local/bin/ibs-recovery'
        tree = ast.parse(source.read_text())
        tree.body = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef))]
        gui = {}
        exec(compile(tree, str(source), 'exec'), gui)
        with tempfile.TemporaryDirectory(dir=ROOT, prefix='.r4-test-') as tmp:
            folder = Path(tmp) / 'ISO con spazi,è'
            folder.mkdir()
            for origin in ('NAS QNAP', 'USB Ventoy'):
                for name in ('WinRE, prova.ISO', 'Acronis prova.iso'):
                    path = folder / name
                    path.write_bytes(b'fixture')
                    answers = [origin] + (['fixture-token'] if origin == 'USB Ventoy' else []) + ['', str(path)]
                    gui['dialog'] = Mock(side_effect=answers)
                    gui['backend'] = Mock(side_effect=lambda action, *args: (
                        [{'token': 'fixture-token', 'name': '/dev/mock', 'label': 'fixture', 'size': 1}]
                        if action == 'ventoy-list' else {'path': str(folder)}))
                    self.assertEqual(gui['select_iso'](), str(path))
                    self.assertIn('--filename=' + str(folder) + '/', gui['dialog'].call_args.args)
            gui['dialog'] = Mock(return_value='USB Ventoy')
            gui['backend'] = Mock(return_value=[])
            with self.assertRaisesRegex(RuntimeError, 'Nessuna partizione'):
                gui['select_iso']()

    def test_launch_path_and_kvm_errors_before_open(self):
        with tempfile.TemporaryDirectory(dir=ROOT, prefix='.r4-test-') as tmp, ExitStack() as stack:
            root = Path(tmp) / 'media'
            root.mkdir()
            outside = Path(tmp) / 'outside.iso'
            outside.write_bytes(b'fixture')
            winre = root / 'WinRE, prova.iso'
            winre.write_bytes(b'fixture')
            acronis = root / 'Acronis prova.iso'
            acronis.write_bytes(b'fixture')
            link = root / 'escape.iso'
            link.symlink_to(outside)
            stack.enter_context(patch.object(vm, 'guest_guard'))
            stack.enter_context(patch.object(vm.pwd, 'getpwnam', return_value=SimpleNamespace(pw_dir='/fixture')))
            stack.enter_context(patch.object(vm, 'kvm_available', return_value=False))
            stack.enter_context(patch.object(vm.shutil, 'which', return_value='/mock/qemu'))
            stack.enter_context(patch.object(vm, 'MEDIA_ROOT', root))
            stack.enter_context(patch.object(vm.Path, 'read_text', return_value='MemAvailable: 9999999 kB\n'))
            opened = stack.enter_context(patch.object(vm.os, 'open'))
            process = stack.enter_context(patch.object(vm.subprocess, 'Popen'))
            request = {'kind': 'iso', 'firmware': 'legacy', 'display': ':0'}
            for path, error in ((outside, 'fuori dalla sorgente'), (link, 'fuori dalla sorgente'),
                                (winre, 'WinRE richiede KVM'), (acronis, 'Confermare TCG')):
                with self.subTest(path=path), self.assertRaisesRegex(media.MediaError, error):
                    vm.launch(dict(request, path=str(path)))
            with self.assertRaisesRegex(media.MediaError, 'KVM non esposto'):
                vm.launch(dict(request, kind='disk'))
            with self.assertRaises(FileNotFoundError):
                vm.launch(dict(request, path=str(root / 'missing.iso')))
            opened.assert_not_called()
            process.assert_not_called()

    def test_nas_mount_and_reject_writable_existing_mount(self):
        with tempfile.TemporaryDirectory(dir=ROOT, prefix='.r4-test-') as tmp:
            import json
            for options in ('ro,nosuid,nodev,noexec', 'rw,nosuid,nodev,noexec'):
                def fake(argv, **kwargs):
                    if argv[0] == 'findmnt':
                        return json.dumps({'filesystems': [{'source': '//192.168.20.123/Public',
                            'fstype': 'cifs', 'options': options}]})
                    return ''
                with patch.object(media, 'MEDIA_ROOT', Path(tmp)), patch.object(media, 'guest_guard'), \
                     patch.object(media.os.path, 'ismount', return_value=False), \
                     patch.object(media, 'run', side_effect=fake) as run:
                    if options.startswith('ro,'):
                        self.assertEqual(media.mount_nas(), str(Path(tmp) / 'qnap'))
                        self.assertIn('guest,ro,nosuid,nodev,noexec,vers=3.0,prefixpath=ISO,noperm,file_mode=0444,dir_mode=0555', run.call_args_list[0].args[0])
                    else:
                        with self.assertRaisesRegex(media.MediaError, 'sola lettura'):
                            media.mount_nas()


if __name__ == '__main__':
    unittest.main(verbosity=2)
