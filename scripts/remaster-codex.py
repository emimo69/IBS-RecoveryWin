#!/usr/bin/env python3
"""One candidate from the immutable working ISO; fakeroot, no host changes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / '.build/remaster-codex'
OUTPUT = ROOT / 'IBS-RecoveryWin-2.1-Codex-amd64.hybrid.iso'


def sha(path, algorithm='sha256'):
    h = hashlib.new(algorithm)
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def phase(name, **values):
    WORK.mkdir(parents=True, exist_ok=True)
    state = {'phase': name, 'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), **values}
    (WORK / 'state.json').write_text(json.dumps(state, indent=2))
    print(json.dumps(state), flush=True)


def run(*args):
    print('+ ' + ' '.join(map(str, args)), flush=True)
    subprocess.run(list(map(str, args)), check=True)


def snapshot(root):
    # Compare EVERY original file, ownership, mode, link and extended attribute.
    # Directory mtimes change legitimately when an entry is added.
    result = {}
    for parent, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            path = Path(parent) / name
            st = path.lstat()
            entry = {'mode': st.st_mode, 'uid': st.st_uid, 'gid': st.st_gid,
                     'rdev': st.st_rdev}
            if stat.S_ISREG(st.st_mode):
                entry.update(size=st.st_size, sha256=sha(path))
            elif stat.S_ISLNK(st.st_mode):
                entry['target'] = os.readlink(path)
            if not stat.S_ISLNK(st.st_mode):
                entry['xattrs'] = {k: os.getxattr(path, k).hex() for k in os.listxattr(path)}
            result[str(path.relative_to(root))] = entry
    return result


def worker(base):
    if not os.environ.get('FAKEROOTKEY'):
        raise RuntimeError('Run through fakeroot; never change ownership on the host')
    if OUTPUT.exists() or (WORK / 'root').exists():
        raise RuntimeError('Candidate or work root already exists: no overwrite or repeated build')
    phase('verify-base')
    original_digest = sha(base)
    (WORK / 'base-identity.local.json').write_text(json.dumps({'path': str(base), 'sha256': original_digest}))
    run(sys.executable, ROOT / 'scripts/prepare-codex.py')
    phase('extract-original-readonly')
    original = WORK / 'original.squashfs'
    manifest = WORK / 'sha256sum-original.txt'
    if not manifest.exists():
        run('xorriso', '-osirrox', 'on', '-indev', base,
            '-extract', '/sha256sum.txt', manifest)
    if not original.exists():
        run('xorriso', '-osirrox', 'on', '-indev', base,
            '-extract', '/live/filesystem.squashfs', original)
    original_entries = [line for line in manifest.read_text().splitlines()
                        if line[66:].lstrip('*').removeprefix('./') == 'live/filesystem.squashfs']
    if len(original_entries) != 1 or sha(original) != original_entries[0][:64]:
        raise RuntimeError('Original SquashFS does not match the ISO SHA-256 manifest')
    root = WORK / 'root'
    run('unsquashfs', '-no-progress', '-processors', '2', '-d', root, original)
    phase('snapshot-original')
    before = snapshot(root)
    (WORK / 'original-files.local.json').write_text(json.dumps(before))
    phase('add-codex-only')
    includes = ROOT / 'config/includes.chroot'
    names = [
        'opt/ibs/codex/codex', 'opt/ibs/codex/codex-code-mode-host',
        'usr/local/bin/codex', 'usr/local/bin/ibs-codex-ai',
        'usr/local/lib/ibs-codex/session.py',
        'usr/local/libexec/ibs-codex-desktop-trust',
        'usr/local/share/licenses/codex/LICENSE', 'usr/local/share/licenses/codex/NOTICE',
        'etc/skel/Desktop/ibs-codex-ai.desktop',
        'etc/xdg/autostart/ibs-codex-desktop-trust.desktop',
    ]
    for name in names:
        source, target = includes / name, root / name
        if target.exists() or target.is_symlink():
            raise RuntimeError('Refusing to replace an existing original file: ' + name)
        missing = []
        parent = target.parent
        while not parent.exists():
            missing.append(parent)
            parent = parent.parent
        for directory in reversed(missing):
            directory.mkdir(mode=0o755)
            os.chown(directory, 0, 0)
        shutil.copyfile(source, target)
        executable = (name.startswith('usr/local/bin/') or name.startswith('opt/ibs/codex/'))
        mode = 0o755 if executable or name.endswith('/ibs-codex-ai.desktop') else 0o644
        os.chmod(target, mode)
        os.chown(target, 0, 0)
    for path in root.rglob('auth.json'):
        raise RuntimeError('Authentication file found in image: ' + str(path.relative_to(root)))
    after = snapshot(root)
    changed = [name for name, value in before.items() if after.get(name) != value]
    if changed:
        raise RuntimeError('Original filesystem entries changed: ' + repr(changed[:20]))
    additions = sorted(set(after) - set(before))
    (WORK / 'payload-check.local.json').write_text(json.dumps({
        'original_entries_verified': len(before), 'original_entries_changed': changed,
        'added_entries': additions}, indent=2))
    phase('compress-single-candidate', original_entries_verified=len(before))
    squash = WORK / 'filesystem.squashfs'
    run('mksquashfs', root, squash, '-noappend', '-comp', 'xz', '-b', '131072',
        '-processors', str(min(4, os.cpu_count() or 1)), '-no-progress')
    # Numeric ownership/modes in the compressed image must match extraction.
    listing = subprocess.check_output(['unsquashfs', '-lln', squash], text=True)
    (WORK / 'candidate-listing.local.txt').write_text(listing)
    baseline_listing = subprocess.check_output(['unsquashfs', '-lln', original], text=True)
    def ownership(text):
        result = {}
        for line in text.splitlines():
            if 'squashfs-root' in line:
                prefix, name = line.split('squashfs-root', 1)
                fields = prefix.split()
                if len(fields) >= 2:
                    result[name] = fields[:2]
        return result
    old_ownership, new_ownership = ownership(baseline_listing), ownership(listing)
    if not old_ownership or any(new_ownership.get(k) != v for k, v in old_ownership.items()):
        raise RuntimeError('Compressed image does not preserve original ownership/modes')
    checksum_text = manifest.read_text()
    lines = []
    replacements = 0
    for line in checksum_text.splitlines():
        if line[66:].lstrip('*').removeprefix('./') == 'live/filesystem.squashfs':
            line = sha(squash) + line[64:]
            replacements += 1
        # Boot catalog bytes are regenerated by xorriso and are not user data.
        if line[66:].lstrip('*').removeprefix('./') == 'isolinux/boot.cat':
            continue
        lines.append(line)
    if replacements != 1:
        raise RuntimeError('Unexpected checksum manifest: SquashFS entry missing or duplicated')
    checksums = WORK / 'sha256sum.txt'
    checksums.write_text('\n'.join(lines) + '\n')
    phase('write-single-iso')
    run('xorriso', '-indev', base, '-outdev', OUTPUT,
        '-boot_image', 'any', 'replay',
        '-map', squash, '/live/filesystem.squashfs',
        '-map', checksums, '/sha256sum.txt',
        '-volid', 'IBS_RECOVERYWIN_2_1_CODEX', '-commit', '-end')
    phase('verify-boot-and-original')
    boot = subprocess.check_output(['xorriso', '-indev', OUTPUT,
                                   '-report_el_torito', 'plain', '-report_system_area', 'plain'], text=True)
    if 'BIOS' not in boot or 'UEFI' not in boot or 'MBR isohybrid' not in boot:
        raise RuntimeError('Hybrid BIOS/UEFI boot metadata missing')
    (WORK / 'candidate-boot.local.txt').write_text(boot)
    if sha(base) != original_digest:
        raise RuntimeError('Original ISO identity changed; do not publish')
    digest = sha(OUTPUT)
    OUTPUT.with_suffix(OUTPUT.suffix + '.sha256').write_text(digest + '  ' + OUTPUT.name + '\n')
    phase('BUILT', iso=str(OUTPUT), bytes=OUTPUT.stat().st_size, sha256=digest,
          base_unchanged=True, original_entries_verified=len(before), original_entries_changed=0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--authorized', action='store_true')
    parser.add_argument('--base-iso', type=Path, required=True)
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not args.authorized:
        parser.error('Explicit authorization required; no image built')
    base = args.base_iso.resolve(strict=True)
    if base == OUTPUT.resolve() or base.suffix.lower() != '.iso':
        raise RuntimeError('Unexpected base ISO')
    if args.worker:
        worker(base)
    else:
        run('fakeroot', '--', sys.executable, Path(__file__).resolve(),
            '--authorized', '--worker', '--base-iso', base)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        phase('FAILED', error=str(error))
        raise
