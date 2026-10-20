#!/usr/bin/env python3
"""Tests for _system/tools/week_facts.py. Run: python3 -m unittest _system/tests/test_week_facts.py -v"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / "tools" / "week_facts.py"
WEEK = "2026-W42"  # Mon 2026-10-12 → Sun 2026-10-18

PAGES = {
    "_system/config.json": '{"owner": {"first_name": "Jane", "match": ["jane"], "emails": ["jane.doe@example.com"]}}',
    "log.md": "# Log\n\n## [2026-10-11] sync | old\n## [2026-10-13] ingest | standup 10-13\n"
              "## [2026-10-18] weekly | 2026-W42\n## [2026-10-19] sync | next week\n",
    "wiki/meetings/2026-10-13-standup.md": "---\ntype: meeting\ntitle: Standup (2026-10-13)\n"
                                           "created: 2026-10-18\nupdated: 2026-10-18\ndate: 2026-10-13\n"
                                           "attendees: [\"[[alex-morgan]]\"]\n---\n# Standup\n",
    "wiki/meetings/2026-10-05-standup.md": "---\ntype: meeting\ntitle: Standup (2026-10-05)\n"
                                           "created: 2026-09-01\nupdated: 2026-09-01\ndate: 2026-10-05\n---\n",
    "wiki/decisions/2026-10-14-split.md": "---\ntype: decision\ntitle: Model split\ndate: 2026-10-14\n"
                                          "created: 2026-09-01\nupdated: 2026-09-01\n---\n",
    "wiki/tickets/PROJ-1.md": "---\ntype: ticket\ntitle: \"PROJ-1: mine\"\nstatus: Closed\nkey: PROJ-1\n"
                              "assignee: Jane\ncreated: 2026-09-01\nupdated: 2026-10-19\n---\n"
                              "## Notes & progress\n- 2026-10-15 — Closed after review.\n- 2026-10-02 — started.\n",
    "wiki/tickets/PROJ-2.md": "---\ntype: ticket\ntitle: \"PROJ-2: theirs\"\nstatus: Done (PR merged)\n"
                              "key: PROJ-2\nassignee: \"[[pat-kim]]\"\ncreated: 2026-09-01\n"
                              "updated: 2026-09-01\n---\n## Notes & progress\n- 2026-10-16 — PR merged.\n",
    "wiki/tickets/PROJ-3.md": "---\ntype: ticket\ntitle: \"PROJ-3: closed later\"\nstatus: Closed\nkey: PROJ-3\n"
                              "assignee: Jane\ncreated: 2026-09-01\nupdated: 2026-09-01\n---\n"
                              "- 2026-10-14 — merged.\n- 2026-10-20 — Closed.\n",
    "wiki/tickets/PROJ-4.md": "---\ntype: ticket\ntitle: \"PROJ-4: stuck\"\nstatus: Blocked\nkey: PROJ-4\n"
                              "assignee: Jane\ncreated: 2026-09-01\nupdated: 2026-09-01\n---\n",
    "wiki/tickets/PROJ-5.md": "---\ntype: ticket\ntitle: \"PROJ-5: open\"\nstatus: In Progress\nkey: PROJ-5\n"
                              "assignee: Jane\ncreated: 2026-09-01\nupdated: 2026-10-15\n---\n"
                              "- 2026-10-15 — not done yet.\n",
    "wiki/prs/repo-19.md": "---\ntype: pr\ntitle: \"repo#19: patch\"\nstatus: merged\nauthor: Jane\n"
                           "created: 2026-09-01\nupdated: 2026-09-01\n---\nApproved, merged and deployed 2026-10-14.\n",
    "wiki/prs/repo-20.md": "---\ntype: pr\ntitle: \"repo#20: theirs\"\nstatus: merged\n"
                           "author: \"[[sam-lee]]\"\ncreated: 2026-09-01\nupdated: 2026-09-01\n---\n"
                           "- 2026-10-13 — merged.\n",
    "wiki/prs/repo-21.md": "---\ntype: pr\ntitle: \"repo#21: open\"\nstatus: open\nauthor: Jane\n"
                           "created: 2026-09-01\nupdated: 2026-10-14\n---\n- 2026-10-14 — merged? not yet.\n",
    "wiki/projects/data-watch-agent.md": "---\ntype: project\ntitle: Data Watch agent\nstatus: active\n"
                                         "tags: [agents, automation]\ncreated: 2026-09-01\nupdated: 2026-09-01\n---\n"
                                         "## Timeline\n- 2026-10-16 — shipped Fixer.\n- 2026-10-09 — built.\n"
                                         "## Related\n- 2026-10-15 — not a timeline bullet.\n",
    "wiki/projects/nht-detection.md": "---\ntype: project\ntitle: NHT detection\nstatus: active\ntags: [bots]\n"
                                      "created: 2026-09-01\nupdated: 2026-09-01\n---\n## Timeline\n"
                                      "- 2026-10-14 — design review.\n",
    "wiki/projects/quiet.md": "---\ntype: project\ntitle: Quiet\nstatus: active\ntags: [automation]\n"
                              "created: 2026-09-01\nupdated: 2026-09-01\n---\n## Timeline\n- 2026-10-01 — x.\n",
    "wiki/people/alex-morgan.md": "---\ntype: person\ntitle: Alex Morgan\ncreated: 2026-09-01\n"
                                     "updated: 2026-09-01\n---\n"
                                     "- [x] Done in week #todo/follow-up ✅ 2026-10-14\n"
                                     "- [x] Done before #todo/follow-up ✅ 2026-10-10\n"
                                     "- [ ] Overdue one #todo/follow-up 📅 2026-10-14\n"
                                     "- [ ] Due later this week #todo/follow-up 📅 2026-10-17\n"
                                     "- [ ] Next week one #todo/review 📅 2026-10-21\n"
                                     "- [ ] Not a todo 📅 2026-10-01\n"
                                     "```\n- [ ] fenced #todo/idea 📅 2026-10-01\n```\n",
    "journal/2026-10-13.md": "---\ntype: daily\ndate: 2026-10-13\n---\n- [ ] Journal add #todo/idea\n",
    "_system/state/digests/2026-10-16-0830.md": "---\ntype: digest\nstatus: pending\n---\n",
    "_system/state/digests/2026-10-15-0830.md": "---\ntype: digest\nstatus: applied\n---\n",
}


class WeekFactsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for relpath, text in PAGES.items():
            p = self.root / relpath
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def run_tool(self, week=WEEK, now="2026-10-16"):
        env = dict(os.environ, VAULT_ROOT=str(self.root), SYNC_NOW=now)
        args = [sys.executable, str(TOOL), "--json"] + (["--week", week] if week else [])
        r = subprocess.run(args, env=env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    def keys(self, items, field="path"):
        return sorted(Path(i[field]).stem if field == "path" else i[field] for i in items)

    def test_week_range(self):
        f = self.run_tool()
        self.assertEqual((f["week"], f["start"], f["end"]), (WEEK, "2026-10-12", "2026-10-18"))
        f = self.run_tool(week="2026-W01")
        self.assertEqual((f["start"], f["end"]), ("2025-12-29", "2026-01-04"))

    def test_default_week_is_current(self):
        self.assertEqual(self.run_tool(week=None, now="2026-10-23")["week"], "2026-W43")

    def test_bad_week_fails(self):
        env = dict(os.environ, VAULT_ROOT=str(self.root))
        r = subprocess.run([sys.executable, str(TOOL), "--week", "2026-43"], env=env, capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)

    def test_log_entries_in_range(self):
        self.assertEqual([e["title"] for e in self.run_tool()["log"]], ["standup 10-13", "2026-W42"])

    def test_meetings_and_decisions_by_date(self):
        f = self.run_tool()
        self.assertEqual(self.keys(f["meetings"]), ["2026-10-13-standup"])
        self.assertEqual(f["meetings"][0]["attendees"], ["[[alex-morgan]]"])
        self.assertEqual(self.keys(f["decisions"]), ["2026-10-14-split"])

    def test_pages_created_and_updated_from_frontmatter(self):
        f = self.run_tool()
        self.assertIn("wiki/meetings/2026-10-13-standup.md", f["pages_created"])
        self.assertIn("wiki/tickets/PROJ-5.md", f["pages_updated"])
        self.assertNotIn("wiki/tickets/PROJ-1.md", f["pages_updated"])

    def test_tickets_closed_use_latest_closing_bullet(self):
        f = self.run_tool()
        self.assertEqual(self.keys(f["tickets_closed"], "key"), ["PROJ-1", "PROJ-2"])
        self.assertEqual(self.run_tool(week="2026-W43")["tickets_closed"][0]["key"], "PROJ-3")

    def test_prs_merged(self):
        f = self.run_tool()
        self.assertEqual(self.keys(f["prs_merged"]), ["repo-19", "repo-20"])
        self.assertEqual([p["merged"] for p in f["prs_merged"]], ["2026-10-14", "2026-10-13"])

    def test_todos(self):
        f = self.run_tool()
        self.assertEqual([t["text"][:12] for t in f["todos_done"]], ["Done in week"])
        self.assertEqual([t["text"][:11] for t in f["todos_overdue"]], ["Overdue one"])
        self.assertEqual([t["text"][:13] for t in f["todos_next_week"]], ["Next week one"])
        self.assertEqual([t["text"][:11] for t in f["todos_added"]], ["Journal add"])

    def test_overdue_at_week_end_for_past_weeks(self):
        f = self.run_tool(now="2026-11-30")
        self.assertEqual(sorted(t["text"][:7] for t in f["todos_overdue"]), ["Due lat", "Overdue"])

    def test_blocked_and_digests(self):
        f = self.run_tool()
        self.assertEqual(self.keys(f["blocked"], "key"), ["PROJ-4"])
        self.assertEqual(f["digests_pending"], ["_system/state/digests/2026-10-16-0830.md"])

    def test_my_open_tickets(self):
        self.assertEqual(self.keys(self.run_tool()["my_tickets_open"], "key"), ["PROJ-4", "PROJ-5"])

    def test_projects_active_from_timeline_only(self):
        f = self.run_tool()
        self.assertEqual(self.keys(f["projects_active"]), ["data-watch-agent", "nht-detection"])
        dw = next(p for p in f["projects_active"] if p["path"].endswith("data-watch-agent.md"))
        self.assertEqual(dw["last"], "2026-10-16")
        self.assertEqual(len(dw["bullets"]), 1)

    def test_wins_only_mine_and_automation(self):
        wins = self.run_tool()["wins"]
        self.assertEqual(sorted((w["kind"], w["link"]) for w in wins),
                         [("automation", "[[data-watch-agent]]"), ("pr", "[[repo-19]]"), ("ticket", "[[PROJ-1]]")])

    def test_git_history_counts(self):
        def git(*a, date="2026-10-14T10:00:00"):
            env = dict(os.environ, GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date,
                       GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@x", GIT_COMMITTER_NAME="t",
                       GIT_COMMITTER_EMAIL="t@x")
            subprocess.run(["git", "-C", str(self.root), *a], env=env, check=True, capture_output=True)
        git("init", "-q")
        git("add", "-A")
        git("commit", "-q", "-m", "seed", date="2026-10-01T10:00:00")
        p = self.root / "wiki/ideas/new-idea.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("---\ntype: idea\ntitle: New\n---\n- [ ] Git-added box #todo/idea\n", encoding="utf-8")
        nht = self.root / "wiki/projects/nht-detection.md"
        nht.write_text(nht.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        git("add", "-A")
        git("commit", "-q", "-m", "week")
        f = self.run_tool()
        self.assertIn("wiki/ideas/new-idea.md", f["pages_created"])
        self.assertIn("wiki/projects/nht-detection.md", f["pages_updated"])
        self.assertIn("Git-added box #todo/idea", [t["text"] for t in f["todos_added"]])

    def test_read_only(self):
        before = {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.run_tool()
        after = {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
