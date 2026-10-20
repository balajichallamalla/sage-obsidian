#!/usr/bin/env python3
"""Tests for _system/tools/run_lock.py. Run: python3 -m unittest _system/tests/test_run_lock.py -v"""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / "tools" / "run_lock.py"


class RunLockTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.lock = Path(self.tmp.name) / "run.lock"

    def tearDown(self):
        self.tmp.cleanup()

    def cli(self, *args, now="2026-10-19T12:00:00Z"):
        env = dict(os.environ, RUN_LOCK=str(self.lock), SYNC_NOW=now)
        return subprocess.run([sys.executable, str(TOOL), *args], env=env, capture_output=True, text=True)

    def test_acquire_release_cycle(self):
        self.assertEqual(self.cli("status").stdout.strip(), "free")
        r = self.cli("acquire", "--owner", "sync")
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "acquired"))
        r2 = self.cli("acquire", "--owner", "daily")
        self.assertEqual(r2.returncode, 3)
        self.assertIn("held by sync since 2026-10-19T12:00:00Z", r2.stdout)
        self.assertEqual(self.cli("release").returncode, 0)
        self.assertEqual(self.cli("acquire", "--owner", "daily").returncode, 0)

    def test_stale_lock_is_replaced(self):
        self.cli("acquire", "--owner", "sync")
        r = self.cli("acquire", "--owner", "todo-sync", now="2026-10-19T14:30:00Z")
        self.assertEqual(r.returncode, 0)
        self.assertIn("replaced stale lock held by sync", r.stdout)
        self.assertIn("held by todo-sync", self.cli("status", now="2026-10-19T14:31:00Z").stdout)

    def test_release_when_free_is_ok(self):
        self.assertEqual(self.cli("release").returncode, 0)


if __name__ == "__main__":
    unittest.main()
