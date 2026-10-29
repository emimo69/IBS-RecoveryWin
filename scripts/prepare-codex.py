#!/usr/bin/env python3
"""Prepare the pinned native CLI in a new source tree; never build an ISO."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


def prepare_component(release, component, filename):
    expected_url = ('https://github.com/openai/codex/releases/download/'
                    + release['tag'] + '/' + component['asset'])
    if component['url'] != expected_url:
        raise RuntimeError('Unexpected upstream URL')
    cache = ROOT / '.build/codex' / release['version']
    cache.mkdir(parents=True, exist_ok=True)
    archive = cache / component['asset']
    if not archive.exists():
        partial = archive.with_suffix('.partial')
        try:
            request = urllib.request.Request(component['url'], headers={'User-Agent': 'IBS-RecoveryWin-build'})
            with urllib.request.urlopen(request, timeout=30) as response, partial.open('wb') as output:
                shutil.copyfileobj(response, output, length=1024 * 1024)
            if partial.stat().st_size != component['bytes'] or digest(partial) != component['sha256']:
                raise RuntimeError('Upstream archive size/SHA-256 mismatch; nothing installed')
            partial.rename(archive)
        finally:
            if partial.exists():
                partial.unlink()
    if archive.stat().st_size != component['bytes'] or digest(archive) != component['sha256']:
        raise RuntimeError('Cached archive SHA-256 mismatch; nothing installed')
    target = ROOT / 'config/includes.chroot/opt/ibs/codex' / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    name = component['asset'].removesuffix('.tar.gz')
    # Never extract paths supplied by an archive, links, or unexpected entries.
    with tarfile.open(archive, 'r:gz') as bundle:
        members = bundle.getmembers()
        if len(members) != 1 or members[0].name != name or not members[0].isfile():
            raise RuntimeError('Unexpected Codex archive structure')
        if members[0].size > 512 * 1024 * 1024:
            raise RuntimeError('Codex executable exceeds the preparation limit')
        with bundle.extractfile(members[0]) as source, target.open('wb') as output:
            shutil.copyfileobj(source, output, length=1024 * 1024)
    os.chmod(target, 0o755)
    return digest(target) + '  /opt/ibs/codex/' + filename + '\n'


def main():
    release = json.loads((ROOT / 'assets/codex-release.json').read_text())
    checksum = prepare_component(release, release, 'codex')
    checksum += prepare_component(release, release['code_mode_host'], 'codex-code-mode-host')
    sums = ROOT / 'config/includes.chroot/usr/local/share/ibs-codex/codex-binary.sha256'
    sums.parent.mkdir(parents=True, exist_ok=True)
    sums.write_text(checksum, encoding='ascii')
    license_dir = ROOT / 'config/includes.chroot/usr/local/share/licenses/codex'
    license_dir.mkdir(parents=True, exist_ok=True)
    for name in ('LICENSE', 'NOTICE'):
        shutil.copyfile(ROOT / 'licenses/codex' / name, license_dir / name)
    for path in ('config/hooks/normal/0200-codex-ai.hook.chroot',
                 'config/includes.chroot/usr/local/bin/codex',
                 'config/includes.chroot/usr/local/bin/ibs-codex-ai',
                 'config/includes.chroot/etc/skel/Desktop/ibs-codex-ai.desktop'):
        os.chmod(ROOT / path, 0o755)
    print('Prepared Codex ' + release['version'] + '; archive SHA-256 verified. No ISO built.')


if __name__ == '__main__':
    main()
