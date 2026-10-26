#!/usr/bin/env python3
"""Harmless CLI comparison; emit only fixed categories, never raw CLI output.

Run from the host as utente. Does not enable timers or run production tasks.
"""
import json
import os
from pathlib import Path
import subprocess
import sys

PROJECT = Path('/opt/ibs-recoverywin-1.0')
PROMPT = ('Rispondi soltanto OK. Non usare strumenti, non leggere o modificare '
          'file, non eseguire CODEX-TASK.md.')


def probe():
    command = ['codex', '--ask-for-approval', 'never', 'exec', '--sandbox',
               'workspace-write', '-C', str(PROJECT), '--json', PROMPT]
    try:
        result = subprocess.run(command, stdin=subprocess.DEVNULL,
                                capture_output=True, timeout=45)
    except subprocess.TimeoutExpired:
        return {'exit_code': 124, 'category': 'timeout'}
    value = (result.stdout + result.stderr).decode('utf-8', 'replace').lower()
    # Allowlisted signatures only: no paths, account diagnostics or transcript.
    signatures = {
        'filesystem_readonly': 'read-only file system',
        'bubblewrap': 'bwrap:',
        'permission_denied': 'permission denied',
        'operation_not_permitted': 'operation not permitted',
        'quota_429': '429',
        'quota_rate_limit': 'rate limit',
        'auth_unauthorized': 'unauthorized',
        'auth_login_required': 'not logged in',
        'dns': 'dns',
        'network_unreachable': 'network unreachable',
        'thread_started': 'thread.started',
        'turn_completed': 'turn.completed',
    }
    return {'exit_code': result.returncode,
            'signatures': [key for key, match in signatures.items() if match in value]}


def main():
    if os.getuid() == 0 or Path.cwd() != PROJECT:
        sys.exit('Eseguire come utente non root nella directory del progetto.')
    if sys.argv[1:] == ['--probe']:
        print(json.dumps(probe(), sort_keys=True))
        return
    if sys.argv[1:]:
        sys.exit('Uso: python3 automation/diagnose-timer.py')
    direct = probe()
    command = ['systemd-run', '--user', '--wait', '--pipe', '--collect',
               '--property=WorkingDirectory=' + str(PROJECT),
               '--property=NoNewPrivileges=true', '--property=ProtectSystem=strict',
               '--property=ProtectHome=read-only', '--property=PrivateTmp=true',
               '--property=ReadWritePaths=' + str(PROJECT),
               sys.executable, str(Path(__file__).resolve()), '--probe']
    try:
        result = subprocess.run(command, stdin=subprocess.DEVNULL,
                                capture_output=True, timeout=60)
        try:
            service = json.loads(result.stdout)
            if not isinstance(service, dict) or 'exit_code' not in service:
                raise ValueError()
        except (ValueError, TypeError):
            service = {'exit_code': result.returncode,
                       'category': 'systemd_probe_unavailable',
                       'bus_permission_denied': b'Operation not permitted' in result.stderr}
    except subprocess.TimeoutExpired:
        service = {'exit_code': 124, 'category': 'systemd_timeout'}
    print(json.dumps({'direct': direct, 'systemd_same_restrictions': service}, sort_keys=True))


if __name__ == '__main__':
    main()
