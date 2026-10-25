#!/usr/bin/env python3
"""Pure policies/args and real read-only fds on temporary files. No block devices."""
import importlib.util
import fcntl
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path('config/includes.chroot/usr/local/lib/ibs-recovery').resolve()))
import media
import vm

class VMTests(unittest.TestCase):
    def rows(self):
        return media.inventory({'blockdevices':[{'name':'/dev/mock','type':'disk','size':1024,'maj:min':'8:0','serial':'test','mountpoints':[],
          'children':[{'name':'/dev/mock1','type':'part','size':1000,'maj:min':'8:1','label':'OS','mountpoints':[]}]}]})
    def test_disks_mounted_live_ventoy_swap_and_holders_excluded(self):
        for mount in ('/run/live/medium','/media/admin/Windows','[SWAP]'):
            rows=self.rows();rows[1]['mountpoints']=[mount]
            self.assertFalse(vm.disk_candidates(rows))
        rows=self.rows();rows[1]['label']='VTOYEFI'
        self.assertFalse(vm.disk_candidates(rows))
        rows=self.rows();rows[1]['type']='crypt'
        self.assertFalse(vm.disk_candidates(rows))
        rows=self.rows();self.assertEqual(len(vm.disk_candidates(rows)),1)
    def test_requires_kvm_for_os_and_overlay_for_default(self):
        with self.assertRaises(media.MediaError):vm.qemu_args(kind='disk',fd=3,firmware='legacy',kvm=False,overlay='session.qcow2')
        with self.assertRaises(media.MediaError):vm.qemu_args(kind='disk',fd=3,firmware='legacy',kvm=True)
    def test_protected_graph_readonly_fdset_and_paths(self):
        args=vm.qemu_args(kind='disk',fd=5,firmware='uefi',kvm=True,code='/usr/share/OVMF/OVMF_CODE_4M.fd',variables='/run/vars.fd',overlay='/run/session with spaces,è.qcow2',base_format='qcow2',base_driver='file')
        graphs=[json.loads(args[i+1]) for i,x in enumerate(args) if x=='-blockdev']
        self.assertTrue(graphs[0]['read-only']);self.assertTrue(graphs[1]['read-only'])
        self.assertEqual(graphs[0]['filename'],'/dev/fdset/1')
        self.assertEqual(graphs[2]['backing'],'ibs-base')
        self.assertEqual(graphs[2]['file']['filename'],'/run/session with spaces,è.qcow2')
        self.assertIn('host',args);self.assertIn('kvm',args)
        self.assertIn('readonly=on',args[args.index('-drive')+1])
        self.assertNotIn('-snapshot',args)
    def test_iso_legacy_and_tcg(self):
        args=vm.qemu_args(kind='iso',fd=4,firmware='legacy',kvm=False,base_driver='file')
        self.assertIn('tcg',args);self.assertIn('max',args);self.assertIn('order=d',args)
        self.assertNotIn('-drive',args)
        self.assertIn('ide-cd,drive=ibs-base,bus=ibs-ahci.0',args)
    def test_direct_is_separate_and_identity_confirmation(self):
        disk=self.rows()[0]
        self.assertTrue(vm.direct_phrase(disk).startswith('SCRIVI /dev/mock '))
        args=vm.qemu_args(kind='disk',fd=4,firmware='legacy',kvm=True,direct=True)
        graph=json.loads(args[args.index('-blockdev')+1])
        self.assertFalse(graph['read-only'])
        self.assertNotIn('ibs-disk',' '.join(args))
    def test_os_readonly_fd_denies_write_on_fixture(self):
        with tempfile.TemporaryDirectory(dir='/opt/ibs-recoverywin-1.0',prefix='.vm-test-') as tmp:
            path=Path(tmp)/'base con spazi.raw';path.write_bytes(b'fixture')
            fd=os.open(path,os.O_RDONLY|os.O_CLOEXEC)
            try:
                self.assertEqual(fcntl.fcntl(fd,fcntl.F_GETFL)&os.O_ACCMODE,os.O_RDONLY)
                with self.assertRaises(OSError):os.write(fd,b'X')
            finally:os.close(fd)
            self.assertEqual(path.read_bytes(),b'fixture')
    def test_guards_and_exclusive_open_are_present(self):
        source=Path(vm.__file__).read_text()
        self.assertIn('os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC',source)
        self.assertIn("confirmation!=direct_phrase(disk)",source)
        self.assertIn('fresh=read_inventory()',source)
        self.assertIn('pass_fds=(fd,)',source)
        self.assertNotIn('shell=True',source)
if __name__=='__main__':unittest.main(verbosity=2)
