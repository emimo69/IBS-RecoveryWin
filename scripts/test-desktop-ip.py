#!/usr/bin/env python3
import runpy
import unittest
format_ip=runpy.run_path('config/includes.chroot/usr/local/bin/ibs-desktop-ip')['format_addresses']
class IPTests(unittest.TestCase):
    def iface(self,name,addr):
        return {'ifname':name,'operstate':'UP','addr_info':[{'family':'inet','scope':'global','local':addr}]}
    def test_ethernet_wifi_and_change(self):
        self.assertEqual(format_ip([self.iface('eth0','192.0.2.1'),self.iface('wlan0','192.0.2.2')]),'IP eth0: 192.0.2.1\nIP wlan0: 192.0.2.2')
        self.assertEqual(format_ip([self.iface('eth0','192.0.2.3')]),'IP eth0: 192.0.2.3')
    def test_no_ip_down_loopback(self):
        down=self.iface('eth0','192.0.2.1');down['operstate']='DOWN'
        self.assertIn('nessun indirizzo',format_ip([down,self.iface('lo','127.0.0.1')]))
    def test_ipv6(self):
        self.assertIn('2001:db8::1',format_ip([{'ifname':'wlan0','addr_info':[{'family':'inet6','scope':'global','local':'2001:db8::1'}]}]))
unittest.main(verbosity=2)
