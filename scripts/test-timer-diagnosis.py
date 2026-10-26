#!/usr/bin/env python3
"""Offline diagnostic regressions; never launch Codex or systemd."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('diagnosis', Path('automation/diagnose-timer.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class Tests(unittest.TestCase):
    def test_readonly_without_leaking_private_output(self):
        result = subprocess.CompletedProcess([], 1, b'private-output', b'Error: Read-only file system')
        with patch.object(m.subprocess, 'run', return_value=result) as run:
            report = m.probe()
        self.assertEqual(report, {'exit_code': 1, 'signatures': ['filesystem_readonly']})
        command = run.call_args.args[0]
        self.assertIn('workspace-write', command)
        self.assertIn('never', command)
        self.assertNotIn('private-output', json.dumps(report))

    def test_timeout(self):
        with patch.object(m.subprocess, 'run', side_effect=subprocess.TimeoutExpired('codex', 45)):
            self.assertEqual(m.probe(), {'exit_code': 124, 'category': 'timeout'})

    def test_systemd_bus_denial_is_not_a_codex_failure(self):
        denied = subprocess.CompletedProcess([], 1, b'', b'Operation not permitted private-output')
        output = io.StringIO()
        with patch.object(m, 'probe', return_value={'exit_code': 0, 'signatures': []}), \
                patch.object(m.os, 'getuid', return_value=1000), \
                patch.object(m.sys, 'argv', ['diagnose-timer.py']), \
                patch.object(m.subprocess, 'run', return_value=denied), \
                contextlib.redirect_stdout(output):
            m.main()
        result = json.loads(output.getvalue())
        self.assertEqual(result['systemd_same_restrictions']['category'], 'systemd_probe_unavailable')
        self.assertTrue(result['systemd_same_restrictions']['bus_permission_denied'])
        self.assertNotIn('private-output', output.getvalue())


if __name__ == '__main__':
    unittest.main()
