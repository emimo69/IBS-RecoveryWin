#!/usr/bin/env python3
"""Prepare a WIM overlay; rebuilding a boot ISO requires --build-iso authorization."""
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ISO = ROOT / 'config/includes.chroot/opt/ibs/iso/IBS-WinRE.iso'

def run(*args, **kwargs):
    subprocess.run([str(x) for x in args], check=True, **kwargs)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--build-iso', action='store_true', help='Requires explicit user authorization to build ISO images')
    args = parser.parse_args()
    work = ROOT / '.build/winre-overlay'
    if work.exists() and not args.build_iso:
        import tempfile
        work = Path(tempfile.mkdtemp(prefix='winre-overlay-', dir=ROOT / '.build'))
    work.mkdir(parents=True, exist_ok=True)
    run(ROOT / 'scripts/build-clipboard.sh')
    wim = work / 'boot.wim'
    if not wim.exists():
        run('xorriso', '-osirrox', 'on', '-indev', ISO, '-extract', '/SOURCES/BOOT.WIM', wim)
    commands = ''.join('add "{}" "{}"\n'.format(ROOT / source, target) for source, target in [
        ('assets/ibs-clipboard.exe', '/Windows/System32/ibs-clipboard.exe'),
        ('assets/ibs-start.cmd', '/Windows/System32/ibs-start.cmd'),
        ('assets/winpeshl.ini', '/Windows/System32/winpeshl.ini'),
    ])
    run('wimupdate', wim, '1', '--check', input=commands.encode())
    run('wimverify', wim)
    print('Overlay WIM:', wim)
    if not args.build_iso:
        print('WIM pronta; nessuna ISO compilata. Per integrare la WIM serve autorizzazione alla compilazione ISO.')
        return
    output = work / 'IBS-WinRE-integrated.iso'
    # The Windows ISO stores its boot images outside the file tree.
    # Extract their full extents before replacing the boot catalog.
    boot = work / 'boot-images'
    boot.mkdir(exist_ok=True)
    run('xorriso', '-osirrox', 'on', '-indev', ISO, '-extract_boot_images', boot)
    bios = boot / 'eltorito_img1_bios.img'
    uefi = boot / 'eltorito_img2_uefi.img'
    if not bios.is_file() or not uefi.is_file():
        raise RuntimeError('Missing BIOS or UEFI boot image in source WinRE ISO')
    if output.exists():
        output.unlink()
    run('xorriso', '-indev', ISO, '-outdev', output,
        '-boot_image', 'any', 'discard',
        '-map', bios, '/ibs-boot/bios.img',
        '-map', uefi, '/ibs-boot/uefi.img',
        '-map', wim, '/SOURCES/BOOT.WIM',
        '-boot_image', 'any', 'bin_path=/ibs-boot/bios.img',
        '-boot_image', 'any', 'cat_path=/ibs-boot/boot.cat',
        '-boot_image', 'any', 'emul_type=no_emulation',
        '-boot_image', 'any', 'load_size=4096',
        '-boot_image', 'any', 'next',
        '-boot_image', 'any', 'efi_path=/ibs-boot/uefi.img',
        '-boot_image', 'any', 'load_size=512')
    # Keep the source ISO and promote the integrated copy only after successful rebuild.
    original = work / 'IBS-WinRE-original.iso'
    shutil.move(ISO, original)
    shutil.copyfile(output, ISO)
    digest = hashlib.file_digest(ISO.open('rb'), 'sha256').hexdigest()
    (ISO.parent / 'clipboard-integrated.sha256').write_text(digest + '  IBS-WinRE.iso\n')
    (ROOT / 'assets/WinRE-integrated.sha256').write_text(hashlib.file_digest(ISO.open('rb'), 'sha256').hexdigest() + '  ' + str(ISO.relative_to(ROOT)) + '\n')

if __name__ == '__main__':
    main()
