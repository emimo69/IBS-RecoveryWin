#!/usr/bin/env python3
"""Offline static checks: never invoke runner, systemctl, Git network or Codex."""
from pathlib import Path
import configparser
import subprocess

root = Path('/opt/ibs-recoverywin-1.0')
runner = (root / 'automation/task-watch').read_text()
for name in ('task-watch', 'install', 'disable'):
    path = root / 'automation' / name
    subprocess.run(['bash', '-n', str(path)], check=True)
    assert path.stat().st_mode & 0o111
for required in ('flock -n 9', 'git rev-parse "$commit:CODEX-TASK.md"',
                 'completed/$blob', 'git merge --ff-only', 'state/blocked',
                 'git status --porcelain', 'timeout 60 git fetch',
                 'exit_code=$rc', '[[ -t 0 && -t 1 ]]',
                 'codex --ask-for-approval on-request --sandbox workspace-write',
                 '-C "$project"', 'AGENTS.md', 'CODEX-TASK.md'):
    assert required in runner, required
assert runner.index('flock -n 9') < runner.index('git fetch')
assert runner.index('if [[ "$mode" == poll ]]') < runner.index('codex --ask')
for forbidden in ('--dangerously-', 'danger-full-access', '--approve-for-me',
                  'git reset', 'git clean', 'sudo ', 'lb build'):
    assert forbidden not in runner, forbidden
install = (root / 'automation/install').read_text()
assert 'systemctl --user enable' not in install
assert 'systemctl --user start' not in install
assert 'systemctl --user daemon-reload' in install
for kind in ('service', 'timer'):
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    parser.read(root / f'automation/systemd/ibs-task-watch.{kind}')
    if kind == 'timer':
        assert parser['Timer']['OnUnitInactiveSec'] == '2min'
        assert parser['Timer']['Unit'] == 'ibs-task-watch.service'
    else:
        assert parser['Service']['ExecStart'].endswith('/automation/task-watch poll')
        assert parser['Service']['WorkingDirectory'] == str(root)
        assert parser['Service']['NoNewPrivileges'] == 'true'
        assert 'User' not in parser['Service']  # user unit, not root system service
assert '/.task-watch/' in (root / '.gitignore').read_text()
print('OK: sintassi, timer, flock, hash blob, blocco errori, invocazione assistita e installazione inattiva (statico).')
