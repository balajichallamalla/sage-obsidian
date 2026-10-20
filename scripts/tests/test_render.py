#!/usr/bin/env python3
"""Tests for scripts/render_vault.py using a small fixture template.
Run from the repo root: python3 -m unittest discover -s scripts/tests -v"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / "render_vault.py"

TEMPLATE = {
    "modules.json": json.dumps({
        "files": {"todoist": ["_system/workflows/todo-sync.md", "_system/tools/todo_sync.py"],
                  "source:slack": ["_system/sources/slack.md"],
                  "dashboard": ["home.md", "_system/dashboard/*"]},
        "seed": ["index.md", "inbox.md"],
        "dirs": ["raw/meetings", "wiki/people", "journal"]}),
    "CLAUDE.md": "# {{sage.vault.name}} for {{sage.owner.name}}\n"
                 "Templates keep {{title}} and {{date:YYYY-MM-DD}}.\n"
                 "<!-- module:todoist -->\n| `/todo-sync` | todo-sync.md |\n<!-- /module -->\n"
                 "<!-- module:!dashboard -->\nNo dashboard.\n<!-- /module -->\n"
                 "<!-- module:source:slack -->\nSlack channels: {{sage.sources.slack.channels}}\n<!-- /module -->\n",
    "_system/workflows/todo-sync.md": "todo sync for {{sage.owner.first_name}}\n",
    "_system/tools/todo_sync.py": "X = 1\n# module:dashboard\nDASH = True\n# /module\n",
    "_system/sources/slack.md": "slack {{sage.sources.slack.user_id}}\n",
    "home.md": "home\n",
    "_system/dashboard/view.js": "// module:todoist\nconst T = 1;\n// /module\nconst ME = '{{sage.owner.first_name}}';\n",
    "index.md": "# Index\n",
    "inbox.md": "# Inbox\n",
}


def config(**over):
    c = {"schema_version": 1, "owner": {"name": "Jane Doe", "first_name": "Jane"},
         "vault": {"name": "brain"},
         "modules": {"sync": True, "todoist": True, "dashboard": True},
         "sources": {"slack": {"enabled": True, "user_id": "U0EXAMPLE", "channels": ["#a", "#b"]}}}
    for k, v in over.items():
        c[k] = v
    return c


class RenderTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.tpl, self.out = base / "template", base / "vault"
        for rel, text in TEMPLATE.items():
            p = self.tpl / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        self.cfg = base / "config.json"

    def tearDown(self):
        self.tmp.cleanup()

    def render(self, cfg, *extra):
        self.cfg.write_text(json.dumps(cfg), encoding="utf-8")
        return subprocess.run([sys.executable, str(TOOL), "--config", str(self.cfg), "--out", str(self.out),
                               "--template", str(self.tpl), *extra], capture_output=True, text=True)

    def read(self, rel):
        return (self.out / rel).read_text(encoding="utf-8")

    def test_full_render(self):
        r = self.render(config())
        self.assertEqual(r.returncode, 0, r.stderr)
        claude = self.read("CLAUDE.md")
        self.assertIn("# brain for Jane Doe", claude)
        self.assertIn("{{title}} and {{date:YYYY-MM-DD}}", claude)
        self.assertIn("/todo-sync", claude)
        self.assertNotIn("No dashboard.", claude)
        self.assertIn("Slack channels: #a, #b", claude)
        self.assertNotIn("module:", claude)
        self.assertEqual(self.read("_system/tools/todo_sync.py"), "X = 1\nDASH = True\n")
        self.assertEqual(self.read("_system/dashboard/view.js"), "const T = 1;\nconst ME = 'Jane';\n")
        self.assertTrue((self.out / "raw/meetings/.gitkeep").exists())
        self.assertEqual(json.loads(self.read("_system/config.json"))["owner"]["name"], "Jane Doe")
        manifest = json.loads(self.read("_system/.framework-manifest.json"))
        self.assertIn("CLAUDE.md", manifest)
        self.assertNotIn("index.md", manifest)

    def test_modules_off_drop_files_and_blocks(self):
        cfg = config(modules={"sync": False, "todoist": False, "dashboard": False})
        self.assertEqual(self.render(cfg).returncode, 0)
        for rel in ["_system/workflows/todo-sync.md", "_system/sources/slack.md", "home.md", "_system/dashboard/view.js"]:
            self.assertFalse((self.out / rel).exists(), rel)
        claude = self.read("CLAUDE.md")
        self.assertNotIn("/todo-sync", claude)
        self.assertIn("No dashboard.", claude)
        self.assertNotIn("Slack channels", claude)

    def test_source_needs_sync_and_enabled(self):
        cfg = config()
        cfg["sources"]["slack"]["enabled"] = False
        self.render(cfg)
        self.assertFalse((self.out / "_system/sources/slack.md").exists())

    def test_refuses_non_empty_target(self):
        self.out.mkdir()
        (self.out / "notes.md").write_text("mine")
        r = self.render(config())
        self.assertEqual(r.returncode, 2)
        self.assertIn("not empty", r.stderr)

    def test_unknown_placeholder_fails(self):
        (self.tpl / "home.md").write_text("{{sage.owner.nickname}}")
        r = self.render(config())
        self.assertEqual(r.returncode, 2)
        self.assertIn("home.md: unknown placeholder {{sage.owner.nickname}}", r.stderr)

    def test_unclosed_block_fails(self):
        (self.tpl / "home.md").write_text("<!-- module:todoist -->\nx\n")
        self.assertEqual(self.render(config()).returncode, 2)

    def test_update_is_idempotent_and_keeps_notes(self):
        self.render(config())
        (self.out / "index.md").write_text("# Index\n- [[my-page]]\n")
        (self.out / "wiki/people/me.md").write_text("me")
        r = self.render(config(), "--update")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("written: 0", r.stdout)
        self.assertEqual(self.read("index.md"), "# Index\n- [[my-page]]\n")
        self.assertEqual(self.read("wiki/people/me.md"), "me")

    def test_update_removes_disabled_module_files(self):
        self.render(config())
        r = self.render(config(modules={"sync": True, "todoist": False, "dashboard": True}), "--update")
        self.assertIn("_system/workflows/todo-sync.md", r.stdout)
        self.assertFalse((self.out / "_system/workflows/todo-sync.md").exists())
        self.assertNotIn("/todo-sync", self.read("CLAUDE.md"))

    def test_update_requires_existing_vault(self):
        self.out.mkdir()
        (self.out / "x.md").write_text("x")
        r = self.render(config(), "--update")
        self.assertEqual(r.returncode, 2)
        self.assertIn("not a sage-obsidian vault", r.stderr)

    def test_dry_run_writes_nothing(self):
        r = self.render(config(), "--dry-run")
        self.assertEqual(r.returncode, 0)
        self.assertIn("CLAUDE.md", r.stdout)
        self.assertFalse(self.out.exists())


if __name__ == "__main__":
    unittest.main()
