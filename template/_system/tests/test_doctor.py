#!/usr/bin/env python3
"""Tests for _system/tools/doctor.py. Run: python3 -m unittest _system/tests/test_doctor.py -v"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]


class DoctorTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "_system/tests").mkdir(parents=True)
        (self.root / "_system/state/digests").mkdir(parents=True)
        shutil.copytree(HERE / "tools", self.root / "_system/tools")
        (self.root / "_system/tests/check_vault.py").write_text("print('OK: stub (0 problems)')\n")

    def tearDown(self):
        self.tmp.cleanup()

    def doctor(self):
        env = dict(os.environ, VAULT_ROOT=str(self.root))
        r = subprocess.run([sys.executable, str(self.root / "_system/tools/doctor.py"), "--json"],
                           env=env, capture_output=True, text=True, cwd=self.root)
        return r.returncode, {c["name"]: c for c in json.loads(r.stdout)}

    def test_missing_config_fails(self):
        code, res = self.doctor()
        self.assertEqual(code, 1)
        self.assertEqual(res["config"]["status"], "fail")

    def test_healthy_vault(self):
        (self.root / "_system/config.json").write_text(json.dumps(
            {"schema_version": 1, "plugin_version": "0.1.0", "owner": {"first_name": "Jane"},
             "modules": {"dashboard": True}}))
        (self.root / ".obsidian/plugins/dataview").mkdir(parents=True)
        (self.root / ".obsidian/plugins/dataview/main.js").write_text("")
        (self.root / ".obsidian/plugins/dataview/data.json").write_text('{"enableDataviewJs": true}')
        (self.root / ".obsidian/community-plugins.json").write_text('["dataview"]')
        (self.root / "_system/.framework-manifest.json").write_text('{"_system/tools/doctor.py": "x"}')
        for args in (["init", "-q"], ["add", "-A"], ["-c", "user.name=t", "-c", "user.email=t@x", "commit", "-qm", "x"]):
            subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True)
        code, res = self.doctor()
        self.assertEqual(code, 0, res)
        self.assertEqual(res["Dataview"]["status"], "ok")
        self.assertEqual(res["Tasks"]["status"], "warn")
        self.assertEqual(res["git"]["status"], "ok")
        self.assertEqual(res["git remote"]["status"], "ok")
        self.assertEqual(res["validator"]["status"], "ok")

    def test_remote_and_old_schema_fail(self):
        (self.root / "_system/config.json").write_text(json.dumps({"schema_version": 0, "modules": {}}))
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "remote", "add", "origin", "https://example.com/x.git"], cwd=self.root, check=True)
        code, res = self.doctor()
        self.assertEqual(code, 1)
        self.assertEqual(res["config"]["status"], "fail")
        self.assertEqual(res["git remote"]["status"], "fail")

    def test_pending_digest_warns(self):
        (self.root / "_system/config.json").write_text(json.dumps({"schema_version": 1, "modules": {}}))
        (self.root / "_system/state/digests/d.md").write_text("---\ntype: digest\nstatus: pending\n---\n")
        _, res = self.doctor()
        self.assertEqual(res["digests"]["status"], "warn")


if __name__ == "__main__":
    unittest.main()
