#!/bin/sh
set -eu
cd /opt/ibs-recoverywin-1.0
for script in auto/config config/hooks/normal/0100-teamviewer.hook.chroot config/includes.chroot/lib/live/config/0990-ibs-admin config/includes.chroot/usr/local/sbin/ibs-remote; do
    sh -n "$script"
    test -x "$script"
done
(
 . ./config/bootstrap
 . ./config/binary
 test "$LB_DISTRIBUTION" = trixie
 test "$LB_ARCHITECTURE" = amd64
 test "$LB_DEBIAN_INSTALLER" = none
 case "$LB_BOOTAPPEND_LIVE" in
  *'username=admin locales=it_IT.UTF-8 keyboard-layouts=it timezone=Europe/Rome'*) ;;
  *) exit 1 ;;
 esac
)
test -f config/includes.chroot/usr/local/sbin/ibs-remote
! git check-ignore -q config/includes.chroot/usr/local/sbin/ibs-remote
git diff --check
printf '%s\n' 'OK: sintassi shell, configurazione live-build e file necessari. Nessuna build eseguita.'
