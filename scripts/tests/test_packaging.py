#!/usr/bin/env python3
"""Packaging checks: manifests, skills, template placeholders. Run: python3 -m unittest discover -s scripts/tests"""
import json
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ALLOWED_FM = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
ROUTERS = {"ingest": "ingest", "sync": "sync", "sync-status": "sync-status", "ask": "query", "search": "search",
           "lint": "lint", "inbox": "inbox", "daily": "daily", "todo-sync": "todo-sync", "weekly": "weekly",
           "prep": "prep", "dash": "dash"}


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    return {k: v.strip() for k, v in re.findall(r"^([A-Za-z][\w-]*):(.*)$", m.group(1), re.M)} if m else None


class PackagingTest(unittest.TestCase):
    def test_manifests(self):
        plugin = json.loads((REPO / ".claude-plugin/plugin.json").read_text())
        self.assertEqual(plugin["name"], "sage-obsidian")
        self.assertRegex(plugin["version"], r"^\d+\.\d+\.\d+$")
        market = json.loads((REPO / ".claude-plugin/marketplace.json").read_text())
        self.assertEqual([p["name"] for p in market["plugins"]], ["sage-obsidian"])
        self.assertTrue(market["owner"]["name"])
        cfg = json.loads((REPO / "presets/_base.json").read_text())
        self.assertEqual(cfg["plugin_version"], plugin["version"])

    def test_no_top_level_bin(self):
        self.assertFalse((REPO / "bin").exists(), "Cowork refuses plugins with a top-level bin/")

    def test_skill_frontmatter(self):
        skills = sorted((REPO / "skills").glob("*/SKILL.md"))
        self.assertGreaterEqual(len(skills), 16)
        for p in skills:
            fm = frontmatter(p.read_text())
            self.assertIsNotNone(fm, p)
            self.assertLessEqual(set(fm), ALLOWED_FM, f"{p}: only {sorted(ALLOWED_FM)} are allowed")
            self.assertEqual(fm["name"], p.parent.name, p)
            self.assertTrue(10 < len(fm["description"]) < 1000, p)

    def test_routers_point_at_template_workflows(self):
        for skill, wf in ROUTERS.items():
            text = (REPO / f"skills/{skill}/SKILL.md").read_text()
            self.assertIn(f"_system/workflows/{wf}.md", text, skill)
            self.assertIn("_system/config.json", text, skill)
            self.assertTrue((REPO / f"template/_system/workflows/{wf}.md").is_file(), wf)

    def test_every_placeholder_resolves_from_base(self):
        base = json.loads((REPO / "presets/_base.json").read_text())
        for p in (REPO / "template").rglob("*"):
            if not p.is_file() or p.suffix not in {".md", ".py", ".js", ".json", ""}:
                continue
            for key in re.findall(r"\{\{sage\.([A-Za-z0-9_.]+)\}\}", p.read_text(encoding="utf-8")):
                cur = base
                for part in key.split("."):
                    self.assertIn(part, cur, f"{p.relative_to(REPO)}: {{{{sage.{key}}}}} not in presets/_base.json")
                    cur = cur[part]

    def test_presets_cover_every_module(self):
        base = json.loads((REPO / "presets/_base.json").read_text())
        for p in (REPO / "presets").glob("[!_]*.json"):
            preset = json.loads(p.read_text())
            self.assertTrue(preset.get("label") and preset.get("description"), p)
            self.assertEqual(set(preset["modules"]), set(base["modules"]), p)
            self.assertEqual(set(preset["sources"]), set(base["sources"]), p)


if __name__ == "__main__":
    unittest.main()
