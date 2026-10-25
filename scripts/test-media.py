#!/usr/bin/env python3
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('media','config/includes.chroot/usr/local/lib/ibs-recovery/media.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def fixture():
    return m.inventory({'blockdevices':[{'name':'/dev/sdb','type':'disk','tran':'usb','serial':'fixture','size':1000,'maj:min':'8:16','mountpoints':[],
      'children':[{'name':'/dev/sdb1','type':'part','label':'Dati con spazi','fstype':'exfat','maj:min':'8:17','size':900,'mountpoints':['/media/admin/Dati con spazi']},
                  {'name':'/dev/sdb2','type':'part','label':'VTOYEFI','size':100,'maj:min':'8:18','mountpoints':[]},
                  {'name':'/dev/sdb11','type':'part','label':'altro','size':10,'mountpoints':[]}]}]})
class MediaTests(unittest.TestCase):
    def test_renamed_ventoy_already_mounted(self):
        rows=fixture();parts=m.ventoy_candidates(rows)
        self.assertEqual([p['name'] for p in parts],['/dev/sdb1'])
        self.assertEqual(parts[0]['mountpoints'],['/media/admin/Dati con spazi'])
        self.assertNotIn('\\n',parts[0]['mountpoints'][0])
    def test_stale_device_rejected(self):
        rows=fixture();token=m.fingerprint(rows[1]);rows[1]['size']=800
        with self.assertRaises(m.MediaError):m.select_token(rows,token,m.ventoy_candidates)
    def test_spaces_commas_unicode_no_shell(self):
        with tempfile.TemporaryDirectory(dir='/opt/ibs-recoverywin-1.0',prefix='.media-test-') as tmp:
            p=Path(tmp)/'ISO con spazi,è';p.mkdir()
            self.assertEqual(m.clean_path(str(p)),str(p))
            with self.assertRaises(m.MediaError):m.clean_path(str(p)+'\n')
    def test_readonly_bind_and_existing_view(self):
        rows=fixture();token=m.fingerprint(rows[1]);calls=[]
        def fake(argv):
            calls.append(argv)
            if argv[0]=='findmnt':return json.dumps({'filesystems':[{'maj:min':'8:17','options':'ro,nosuid,nodev,noexec'}]})
            return ''
        with tempfile.TemporaryDirectory(dir='/opt/ibs-recoverywin-1.0',prefix='.media-test-') as tmp:
            with patch.object(m,'MEDIA_ROOT',Path(tmp)),patch.object(m,'guest_guard'),patch.object(m,'read_inventory',return_value=rows),patch.object(m,'clean_path',side_effect=lambda p:p),patch.object(m,'run',side_effect=fake),patch.object(m.os.path,'ismount',return_value=False):
                target=m.mount_ventoy(token)
                self.assertIn(['mount','--bind','/media/admin/Dati con spazi',target],calls)
                self.assertIn(['mount','-o','remount,bind,ro,nosuid,nodev,noexec',target],calls)
            calls.clear()
            with patch.object(m,'MEDIA_ROOT',Path(tmp)),patch.object(m,'guest_guard'),patch.object(m,'read_inventory',return_value=rows),patch.object(m,'clean_path',side_effect=lambda p:p),patch.object(m,'run',side_effect=fake),patch.object(m.os.path,'ismount',return_value=True):
                self.assertEqual(m.mount_ventoy(token),target)
                self.assertFalse(any(c[0]=='mount' for c in calls))
    def test_nas_no_password(self):
        source=Path(spec.origin).read_text()
        self.assertIn('guest,ro,nosuid,nodev,noexec,vers=3.0,prefixpath=ISO',source)
        self.assertNotIn('password=',source)
        self.assertNotIn('shell=True',source)
if __name__=='__main__':unittest.main(verbosity=2)
