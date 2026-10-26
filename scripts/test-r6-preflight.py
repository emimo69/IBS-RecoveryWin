#!/usr/bin/env python3
"""Offline fixtures only; never starts QEMU or accesses physical media."""
import argparse
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('r6', Path(__file__).with_name('preflight-r6-winre.py'))
r6 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r6)


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1], prefix='.r6-test-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.args = argparse.Namespace(**{key: str(self.root / key) for key in ('iso', 'code', 'vars', 'base', 'overlay')})
        iso = bytearray(34816)
        iso[32768:32775] = b'\x01CD001\x01'
        Path(self.args.iso).write_bytes(iso)
        self.args.iso_sha256 = hashlib.sha256(iso).hexdigest()
        for key, size in [('code', 3653632), ('vars', 540672)]:
            data = bytearray(size)
            data[40:44] = b'_FVH'
            Path(getattr(self.args, key)).write_bytes(data)
        self.create(self.args.base)
        self.create(self.args.overlay, self.args.base)

    def create(self, path, backing=None):
        argv = ['qemu-img', 'create', '-f', 'qcow2']
        if backing:
            argv += ['-F', 'qcow2', '-b', backing]
        subprocess.run(argv + [path, '4M'], check=True, capture_output=True)

    def test_valid_and_unchanged(self):
        before = {p: r6.digest(p) for p in self.root.iterdir()}
        r6.validate(self.args)
        self.assertEqual(before, {p: r6.digest(p) for p in self.root.iterdir()})

    def test_paths(self):
        for value in ['/dev/null', '/proc/version', '/sys/kernel', '/mnt/a', '/media/a', '/run/media/a', 'relative', str(self.root / '..' / 'a'), str(self.root), str(self.root / 'missing')]:
            with self.subTest(value=value), self.assertRaises((r6.Unsafe, OSError)):
                r6.local_file(value)
        link = self.root / 'link'
        link.symlink_to(self.args.iso)
        with self.assertRaises(r6.Unsafe):
            r6.local_file(str(link))
        fifo = self.root / 'fifo'
        r6.os.mkfifo(fifo)
        with self.assertRaises(r6.Unsafe):
            r6.local_file(str(fifo))

    def test_network_mount(self):
        original = Path.read_text
        def read(p, *a, **kw):
            if str(p) == '/proc/self/mountinfo':
                return '1 0 0:1 / / rw - nfs server:/share rw\n'
            return original(p, *a, **kw)
        with patch.object(Path, 'read_text', read), self.assertRaises(r6.Unsafe):
            r6.local_file(self.args.iso)

    def test_bad_iso_hash(self):
        self.args.iso_sha256 = '0' * 64
        with self.assertRaises(r6.Unsafe):
            r6.validate(self.args)

    def test_bad_iso_structure(self):
        Path(self.args.iso).write_bytes(b'fake')
        self.args.iso_sha256 = r6.digest(Path(self.args.iso))
        with self.assertRaises(r6.Unsafe):
            r6.validate(self.args)

    def test_bad_firmware(self):
        Path(self.args.code).write_bytes(b'fake')
        with self.assertRaises(r6.Unsafe):
            r6.validate(self.args)

    def test_unexpected_backing_before_qemu(self):
        with patch.object(r6.subprocess, 'run', side_effect=AssertionError('must not probe chain')):
            with self.assertRaises(r6.Unsafe):
                r6.qcow(Path(self.args.overlay))
            with self.assertRaises(r6.Unsafe):
                r6.qcow(Path(self.args.overlay), self.root / 'other')

    def test_corrupt_image(self):
        Path(self.args.base).write_bytes(b'QFI\xfb' + bytes(100))
        with self.assertRaises(r6.Unsafe):
            r6.qcow(Path(self.args.base))

    def test_size_mismatch(self):
        subprocess.run(['qemu-img', 'resize', self.args.overlay, '8M'], check=True, capture_output=True)
        with self.assertRaises(r6.Unsafe):
            r6.validate(self.args)

    def test_usb_mount(self):
        original = Path.resolve
        def resolve(p, *a, **kw):
            if str(p).startswith('/sys/dev/block/'):
                return Path('/sys/devices/usb1/fake')
            return original(p, *a, **kw)
        with patch.object(Path, 'resolve', resolve), self.assertRaises(r6.Unsafe):
            r6.local_file(self.args.iso)

    def test_cli_failure(self):
        result = subprocess.run(['python3', str(Path(r6.__file__)), '--iso', '/dev/null'],
                                capture_output=True)
        self.assertNotEqual(result.returncode, 0)

    def test_hardlink(self):
        Path(self.args.overlay).unlink()
        Path(self.args.overlay).hardlink_to(self.args.base)
        with self.assertRaises(r6.Unsafe):
            r6.validate(self.args)


if __name__ == '__main__':
    unittest.main()
