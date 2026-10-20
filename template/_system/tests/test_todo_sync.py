#!/usr/bin/env python3
"""Tests for _system/tools/todo_sync.py. Run: python3 -m unittest _system/tests/test_todo_sync.py -v"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / "tools" / "todo_sync.py"
NOW = "2026-10-19T12:00:00Z"
spec = importlib.util.spec_from_file_location("todo_sync", TOOL)
ts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ts)


class ParseTest(unittest.TestCase):
    def test_open_line_with_alias_link_project_tag_and_due(self):
        p = ts.parse_line("- [ ] Ping [[jane-doe|Jane]] about [[wiki/projects/rollout]] "
                          "#todo/follow-up #nht-detection 📅 2026-10-22")
        self.assertEqual(p["mark"], " ")
        self.assertEqual(p["content"], "Ping Jane about rollout")
        self.assertEqual(p["due"], "2026-10-22")
        self.assertEqual(p["category"], "follow-up")
        self.assertEqual(p["project_tags"], ["nht-detection"])
        self.assertIsNone(p["id"])

    def test_markers_and_ids(self):
        p = ts.parse_line("- [x] Ship it #todo/ticket 📅 2026-10-20 ✅ 2026-10-21 🆔 td:abc123")
        self.assertEqual((p["mark"], p["id"], p["content"]), ("x", "abc123", "Ship it"))
        c = ts.parse_line("- [-] Drop it #todo/idea ❌ 2026-10-21 🆔 td:9")
        self.assertEqual((c["mark"], c["id"]), ("-", "9"))

    def test_slug_links_become_names_but_keys_stay(self):
        p = ts.parse_line("- [ ] Ask [[corey-beus]] about [[PROJ-1835]] and [[rollout]] #todo/follow-up")
        self.assertEqual(p["content"], "Ask Corey Beus about PROJ-1835 and rollout")

    def test_non_todo_lines_ignored(self):
        self.assertIsNone(ts.parse_line("- [ ] no category here"))
        self.assertIsNone(ts.parse_line("- plain bullet #todo/idea"))
        self.assertIsNone(ts.parse_line("- [[page]]: Ping Jane #todo/follow-up"))

    def test_hash_ignores_markers(self):
        a = ts.parse_line("- [ ] Ship it #todo/ticket 📅 2026-10-20")
        b = ts.parse_line("- [x] Ship it #todo/ticket 📅 2026-10-20 ✅ 2026-10-21 🆔 td:1")
        self.assertEqual(a["hash"], b["hash"])
        c = ts.parse_line("- [ ] Ship it #todo/ticket 📅 2026-10-25")
        self.assertNotEqual(a["hash"], c["hash"])


class VaultCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "wiki/projects").mkdir(parents=True)
        (self.root / "journal").mkdir()
        (self.root / "raw/meetings").mkdir(parents=True)
        self.state = self.root / "state.json"
        self.env = dict(os.environ, VAULT_ROOT=str(self.root), SYNC_STATE=str(self.state), SYNC_NOW=NOW)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def cli(self, *args):
        return subprocess.run([sys.executable, str(TOOL), *args], env=self.env,
                              capture_output=True, text=True)

    def plan(self, remote):
        rp = self.root / "remote.json"
        rp.write_text(json.dumps(remote))
        r = self.cli("plan", "--remote", str(rp))
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    def set_state(self, seen):
        self.state.write_text(json.dumps({"sources": {"todoist": {"seen": seen}}}))


class PlanTest(VaultCase):
    def test_first_run_creates_open_only_and_ignores_raw_and_fences(self):
        self.write("wiki/projects/a.md", "# A\n- [ ] One #todo/project #a 📅 2026-10-20\n"
                   "- [x] Done already #todo/ticket\n```\n- [ ] in fence #todo/idea\n```\n")
        self.write("journal/2026-10-19.md", "- [ ] Two #todo/growth\n")
        self.write("raw/meetings/x-raw.md", "- [ ] raw one #todo/idea\n")
        p = self.plan({"open": [], "completed": []})
        self.assertEqual([c["content"] for c in p["create"]], ["One", "Two"])
        one = [c for c in p["create"] if c["content"] == "One"][0]
        self.assertEqual((one["section"], one["due"], one["line_no"]), ("project", "2026-10-20", 2))
        self.assertIn("Vault: wiki/projects/a.md", one["description"])
        self.assertIn("obsidian://open?vault=second-brain&file=wiki/projects/a", one["description"])
        self.assertIn("Project: #a", one["description"])

    def test_all_sync_cases(self):
        h = lambda line: ts.parse_line(line)["hash"]
        lines = {
            "a": "- [ ] Tick me #todo/ticket 🆔 td:a",
            "b": "- [ ] Deleted remotely #todo/ticket 🆔 td:b",
            "c": "- [x] Done in vault #todo/ticket ✅ 2026-10-19 🆔 td:c",
            "d": "- [ ] Edited in vault v2 #todo/ticket 🆔 td:d",
            "f": "- [ ] Rescheduled in Todoist only #todo/ticket 📅 2026-10-20 🆔 td:f",
            "g": "- [-] Cancelled in vault #todo/ticket ❌ 2026-10-19 🆔 td:g",
        }
        self.write("wiki/projects/p.md", "\n".join(lines.values()) + "\n")
        seen = {k: {"path": "wiki/projects/p.md", "hash": h(v), "status": "open"} for k, v in lines.items()}
        seen["d"]["hash"] = h("- [ ] Edited in vault v1 #todo/ticket")
        seen["e"] = {"path": "wiki/projects/old.md", "hash": "x", "status": "open"}
        self.set_state(seen)
        p = self.plan({"open": ["b2", "c", "d", "e", "f", "g"],
                       "completed": [{"id": "a", "completed_at": "2026-10-18T10:00:00Z"}]})
        self.assertEqual([e["id"] for e in p["tick_local"]], ["a"])
        self.assertEqual(p["tick_local"][0]["date"], "2026-10-18")
        self.assertEqual([e["id"] for e in p["cancel_local"]], ["b"])
        self.assertEqual([e["id"] for e in p["complete_remote"]], ["c"])
        self.assertEqual([e["id"] for e in p["update_remote"]], ["d"])
        self.assertEqual(p["update_remote"][0]["content"], "Edited in vault v2")
        self.assertEqual(sorted(e["id"] for e in p["delete_remote"]), ["e", "g"])
        self.assertEqual(p["create"], [])
        self.assertFalse(p["needs_confirm"])

    def test_warnings_for_two_categories_and_duplicate_ids(self):
        self.write("wiki/projects/w.md", "- [ ] Two cats #todo/ticket #todo/review\n"
                   "- [ ] Dup #todo/idea 🆔 td:z\n- [ ] Dup again #todo/idea 🆔 td:z\n")
        p = self.plan({"open": ["z"], "completed": []})
        self.assertEqual(p["create"], [])
        self.assertTrue(any("exactly one" in w for w in p["warnings"]))
        self.assertTrue(any("duplicate id td:z" in w for w in p["warnings"]))

    def test_needs_confirm_when_many_cancellations(self):
        body = "".join(f"- [ ] T{i} #todo/ticket 🆔 td:{i}\n" for i in range(5))
        self.write("wiki/projects/m.md", body)
        self.set_state({str(i): {"path": "wiki/projects/m.md", "hash": "x", "status": "open"} for i in range(5)})
        p = self.plan({"open": [], "completed": []})
        self.assertEqual(len(p["cancel_local"]), 5)
        self.assertTrue(p["needs_confirm"])


class ApplyTest(VaultCase):
    def test_apply_writes_markers_and_state(self):
        self.write("wiki/projects/a.md", "- [ ] New one #todo/project\n"
                   "- [ ] Tick me #todo/ticket 🆔 td:a\n- [ ] Gone #todo/ticket 🆔 td:b\n"
                   "- [x] Vault done #todo/ticket 🆔 td:c\n")
        self.set_state({k: {"path": "wiki/projects/a.md", "hash": "h", "status": "open"} for k in "abc"})
        p = self.plan({"open": ["c"], "completed": [{"id": "a", "completed_at": "2026-10-18"}]})
        p["create"][0]["id"] = "n1"
        rp = self.root / "results.json"
        rp.write_text(json.dumps(p))
        r = self.cli("apply", str(rp))
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(out["applied"]["create"], 1)
        text = (self.root / "wiki/projects/a.md").read_text().splitlines()
        self.assertEqual(text[0], "- [ ] New one #todo/project 🆔 td:n1")
        self.assertEqual(text[1], "- [x] Tick me #todo/ticket ✅ 2026-10-18 🆔 td:a")
        self.assertEqual(text[2], "- [-] Gone #todo/ticket ❌ 2026-10-19 🆔 td:b")
        self.assertEqual(text[3], "- [x] Vault done #todo/ticket ✅ 2026-10-19 🆔 td:c")
        st = json.loads(self.state.read_text())["sources"]["todoist"]
        self.assertEqual(st["seen"]["n1"]["status"], "open")
        self.assertEqual((st["seen"]["a"]["status"], st["seen"]["b"]["status"], st["seen"]["c"]["status"]),
                         ("done", "cancelled", "done"))
        self.assertEqual(st["cursor"], NOW)
        self.assertEqual(st["last_run"]["status"], "ok")

    def test_apply_bumps_updated_in_frontmatter(self):
        self.write("wiki/projects/a.md", "---\ntype: project\nupdated: 2026-01-01\n---\n- [ ] New one #todo/project\n")
        p = self.plan({"open": [], "completed": []})
        p["create"][0]["id"] = "n1"
        rp = self.root / "results.json"
        rp.write_text(json.dumps(p))
        self.cli("apply", str(rp))
        self.assertIn("updated: 2026-10-19", (self.root / "wiki/projects/a.md").read_text())

    def test_apply_skips_line_changed_after_plan(self):
        self.write("wiki/projects/a.md", "- [ ] New one #todo/project\n")
        p = self.plan({"open": [], "completed": []})
        p["create"][0]["id"] = "n1"
        self.write("wiki/projects/a.md", "- [ ] New one, edited #todo/project\n")
        rp = self.root / "results.json"
        rp.write_text(json.dumps(p))
        out = json.loads(self.cli("apply", str(rp)).stdout)
        self.assertEqual(out["applied"]["create"], 0)
        self.assertEqual(out["skipped"][0]["reason"], "line changed since plan")
        self.assertNotIn("🆔", (self.root / "wiki/projects/a.md").read_text())

    def test_status_and_record_project(self):
        self.write("wiki/projects/a.md", "- [ ] Open #todo/project\n- [x] Done #todo/project 🆔 td:1\n")
        sp = self.root / "sections.json"
        sp.write_text(json.dumps({"project": "s1"}))
        r = self.cli("record-project", "P1", str(sp))
        self.assertEqual(r.returncode, 0, r.stderr)
        st = json.loads(self.state.read_text())["sources"]["todoist"]
        self.assertEqual((st["project_id"], st["sections"]["project"]), ("P1", "s1"))
        out = self.cli("status").stdout
        self.assertIn("project", out)
        self.assertIn("no-id", out)


if __name__ == "__main__":
    unittest.main()
