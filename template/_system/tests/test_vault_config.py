#!/usr/bin/env python3
"""Tests for _system/tools/vault_config.py. Run: python3 -m unittest _system/tests/test_vault_config.py -v"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import vault_config  # noqa: E402


class VaultConfigTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = os.environ.get("VAULT_ROOT")
        os.environ["VAULT_ROOT"] = self.tmp.name
        (Path(self.tmp.name) / "_system").mkdir()

    def tearDown(self):
        if self.old is None:
            os.environ.pop("VAULT_ROOT", None)
        else:
            os.environ["VAULT_ROOT"] = self.old
        self.tmp.cleanup()

    def write(self, cfg):
        (Path(self.tmp.name) / "_system/config.json").write_text(json.dumps(cfg))

    def test_missing_config_is_empty(self):
        self.assertEqual(vault_config.load(), {})
        self.assertFalse(vault_config.is_owner("Jane"))

    def test_owner_match_list(self):
        self.write({"owner": {"first_name": "Jane", "match": ["jane", "jdoe"], "emails": ["Jane.Doe@Example.com"]},
                    "modules": {"todoist": True}})
        self.assertTrue(vault_config.is_owner("[[jane-doe]]"))
        self.assertTrue(vault_config.is_owner("JDoe"))
        self.assertFalse(vault_config.is_owner("[[alex-morgan]]"))
        self.assertEqual(vault_config.owner_emails(), {"jane.doe@example.com"})
        self.assertTrue(vault_config.module_on("todoist"))
        self.assertFalse(vault_config.module_on("dashboard"))

    def test_first_name_fallback(self):
        self.write({"owner": {"first_name": "Jane"}})
        self.assertTrue(vault_config.is_owner("Jane (me)"))


if __name__ == "__main__":
    unittest.main()
