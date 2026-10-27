#!/usr/bin/env python3
"""Integrate the clipboard agent while preserving WinRE's UDF filesystem."""
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ISO = ROOT / 'config/includes.chroot/opt/ibs/iso/IBS-WinRE.iso'
ORIGINAL = ROOT / '.build/winre-overlay/IBS-WinRE-original.iso'


def run(*args, **kwargs):
    subprocess.run([str(x) for x in args], check=True, **kwargs)


def sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--build-iso', action='store_true', help='Build an integrated WinRE ISO')
    args = parser.parse_args()

    work = ROOT / '.build/winre-overlay'
    work.mkdir(parents=True, exist_ok=True)
    source = ORIGINAL if ORIGINAL.is_file() else ISO
    if not source.is_file():
        raise FileNotFoundError(f'WinRE ISO non trovata: {source}')

    run(ROOT / 'scripts/build-clipboard.sh')
    base_wim = work / 'boot-original.wim'
    if not base_wim.exists():
        run('7z', 'e', '-y', f'-o{work}', source, 'sources/boot.wim')
        extracted = work / 'boot.wim'
        if not extracted.is_file():
            raise RuntimeError('L’ISO WinRE non contiene sources/boot.wim nel filesystem UDF')
        shutil.move(extracted, base_wim)
    wim = work / 'boot.wim'
    shutil.copyfile(base_wim, wim)
    commands = ''.join('add "{}" "{}"\n'.format(ROOT / source_path, target) for source_path, target in [
        ('assets/ibs-clipboard.exe', '/Windows/System32/ibs-clipboard.exe'),
        ('assets/ibs-start.cmd', '/Windows/System32/ibs-start.cmd'),
        ('assets/winpeshl.ini', '/Windows/System32/winpeshl.ini'),
    ])
    run('wimupdate', wim, '1', '--check', input=commands.encode())
    run('wimverify', wim)
    print('Overlay WIM:', wim)
    if not args.build_iso:
        print('WIM pronta; nessuna ISO creata. Usare --build-iso per generare la ISO WinRE.')
        return

    tree = ROOT / '.build/winre-udf-source'
    if tree.exists():
        shutil.rmtree(tree)
    tree.mkdir(parents=True)
    run('7z', 'x', '-y', f'-o{tree}', source)
    full_wim = tree / 'sources/boot.wim'
    bcd = tree / 'EFI/Microsoft/Boot/BCD'
    if not bcd.is_file():
        raise RuntimeError('BCD UEFI mancante: il filesystem UDF non è stato estratto integralmente')
    shutil.copyfile(wim, full_wim)

    boot = work / 'boot-images'
    if boot.exists():
        shutil.rmtree(boot)
    boot.mkdir(exist_ok=True)
    run('xorriso', '-osirrox', 'on', '-indev', source, '-extract_boot_images', boot)
    bios = boot / 'eltorito_img1_bios.img'
    uefi = boot / 'eltorito_img2_uefi.img'
    if not bios.is_file() or not uefi.is_file():
        raise RuntimeError('Immagini di boot BIOS/UEFI mancanti nell’ISO sorgente')
    boot_dir = tree / 'ibs-boot'
    boot_dir.mkdir(exist_ok=True)
    shutil.copyfile(bios, boot_dir / 'bios.img')
    shutil.copyfile(uefi, boot_dir / 'uefi.img')

    output = work / 'IBS-WinRE-integrated.iso'
    output.unlink(missing_ok=True)
    run('genisoimage', '-udf', '-iso-level', '3', '-full-iso9660-filenames',
        '-relaxed-filenames', '-D', '-N', '-V', 'CD_ROM',
        '-b', 'ibs-boot/bios.img', '-no-emul-boot', '-boot-load-size', '8',
        '-eltorito-alt-boot', '-e', 'ibs-boot/uefi.img', '-no-emul-boot',
        '-o', output, tree)

    # Validate the full UDF paths before replacing the integrated asset.
    listing = subprocess.run(['7z', 'l', output], check=True, capture_output=True, text=True).stdout
    for required in ('EFI/Microsoft/Boot/BCD', 'sources/boot.wim'):
        if required.lower() not in listing.lower():
            raise RuntimeError(f'Percorso UDF richiesto non trovato nella ISO: {required}')
    run('wimverify', full_wim)

    ISO.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(output, ISO)
    digest = sha256(ISO)
    (ISO.parent / 'clipboard-integrated.sha256').write_text(digest + '  IBS-WinRE.iso\n')
    (ROOT / 'assets/WinRE-integrated.sha256').write_text(
        digest + '  ' + str(ISO.relative_to(ROOT)) + '\n')
    print('ISO WinRE UDF integrata:', ISO)
    print('SHA256:', digest)


if __name__ == '__main__':
    main()
