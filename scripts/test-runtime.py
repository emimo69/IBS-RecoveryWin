#!/usr/bin/env python3
import errno
import json
import os
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'config/includes.chroot/usr/local/lib'))
from ibs2.clipboard import Frames, frame, LIMIT, READY
from ibs2.disks import open_disks, inventory
from ibs2.vm import command

class ClipboardTests(unittest.TestCase):
    def test_fragmented_and_coalesced_unicode(self):
        data = frame('caffè € 文字\r\nseconda riga') + frame('')
        parser=Frames();messages=[]
        for value in data:
            messages += parser.feed(bytes([value]))
        self.assertEqual(messages,['caffè € 文字\r\nseconda riga',''])
    def test_handshake(self):
        self.assertEqual(Frames().feed(struct.pack('<4sI',b'IBC2',READY)),[None])
    def test_bad_input(self):
        for data in [b'FAIL'+struct.pack('<I',0),b'IBC2'+struct.pack('<I',LIMIT+1),
                     b'IBC2'+struct.pack('<I',1)+b'\xff',b'IBC2'+struct.pack('<I',1)+b'\0']:
            with self.subTest(data=data), self.assertRaises((ValueError,UnicodeError)):
                Frames().feed(data)

class DiskTests(unittest.TestCase):
    @patch('ibs2.disks.inventory')
    @patch('ibs2.disks.os.open')
    def test_reject_mounted_swap_and_unknown_before_open(self, opened, listing):
        listing.return_value=[{'path':'/dev/testdisk','blocked':'montato','type':'disk'}]
        for paths in [['/dev/testdisk'],['/dev/unknown'],['/etc/passwd'],['/dev/testdisk']*2,['/dev/x'+str(i) for i in range(6)]]:
            with self.subTest(paths=paths),self.assertRaises(ValueError):
                open_disks(paths)
        opened.assert_not_called()
    def test_real_inventory_only_read_operations(self):
        # Actual host inventory, never open any physical device.
        for disk in inventory():
            self.assertEqual(disk['type'],'disk')
            self.assertIn('blocked',disk)
    @patch('ibs2.disks.inventory',return_value=[{'path':'/dev/testdisk','blocked':''}])
    @patch('ibs2.disks.os.stat')
    @patch('ibs2.disks.os.open',side_effect=OSError(errno.EBUSY,'busy'))
    def test_kernel_claim_failure(self, opened, stated, listing):
        stated.return_value.st_mode=0o060660
        with self.assertRaises(OSError):open_disks(['/dev/testdisk'])
        self.assertTrue(opened.call_args.args[1] & os.O_EXCL)
    @patch('ibs2.disks.inventory',return_value=[{'path':'/dev/testdisk','blocked':''}])
    @patch('ibs2.disks.os.stat')
    @patch('ibs2.disks.os.fstat')
    @patch('ibs2.disks.os.close')
    @patch('ibs2.disks.os.open',side_effect=[33,34])
    def test_identity_race_closes_both_descriptors(self, opened, closed, fstated, stated, listing):
        stated.return_value.st_mode=0o060660;stated.return_value.st_rdev=100
        fstated.return_value.st_rdev=200
        with self.assertRaises(ValueError):open_disks(['/dev/testdisk'])
        self.assertEqual({c.args[0] for c in closed.call_args_list},{33,34})
    @patch('ibs2.vm.os.fstat')
    def test_fdset_rw_and_sector_geometry(self, stated):
        stated.return_value.st_mode = 0o060660
        args=command(Path('/run/user/1000/test'),[(33,{'_probe_fd':34,'log-sec':4096,'phy-sec':4096})],acceleration='tcg')
        joined=' '.join(args)
        self.assertIn('fd=33,set=1',joined)
        self.assertIn('fd=34,set=1',joined)
        self.assertIn('file=/dev/fdset/1,format=raw',joined)
        self.assertIn('file.driver=host_device',joined)
        self.assertIn('nvme,drive=physical0', joined)
        self.assertIn('logical_block_size=4096,physical_block_size=4096',joined)
        self.assertIn('guestfwd=tcp:10.0.2.100:17625-chardev:clip',joined)
        self.assertNotIn('hostfwd',joined)
        self.assertNotIn('snapshot',joined)
        self.assertNotIn('/dev/sd',joined)

if __name__ == '__main__':unittest.main(verbosity=2)
