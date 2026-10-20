#!/usr/bin/env python3
"""Tests for _system/tools/dash_snapshot.py. Run: python3 -m unittest _system/tests/test_dash_snapshot.py -v"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / "tools" / "dash_snapshot.py"
NOW = "2026-10-21T14:00:00Z"  # Wednesday of 2026-W43


class DashSnapshotTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "_system/state").mkdir(parents=True)
        self.file = self.root / "_system/state/dashboard.json"

    def tearDown(self):
        self.tmp.cleanup()

    def run_tool(self, *args, now=NOW):
        env = dict(os.environ, VAULT_ROOT=str(self.root), SYNC_NOW=now)
        return subprocess.run([sys.executable, str(TOOL), *args], env=env, capture_output=True, text=True)

    def write(self, part, now=NOW):
        p = self.root / "part.json"
        p.write_text(json.dumps(part), encoding="utf-8")
        r = self.run_tool("write", str(p), now=now)
        return r, (json.loads(self.file.read_text()) if self.file.exists() else None)

    def test_calendar_sorted_and_large_flag(self):
        r, d = self.write({"calendar": [{"start": "11:15", "title": "All hands", "attendees": 17},
                                        {"start": "09:00", "title": "Standup", "attendees": 10}]})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual([e["title"] for e in d["calendar"]], ["Standup", "All hands"])
        self.assertEqual([e["large"] for e in d["calendar"]], [False, True])
        self.assertEqual(d["sources"]["calendar"], {"at": NOW, "ok": True, "note": "", "data_at": NOW})

    def test_hours_only_mine_only_this_week(self):
        logs = [{"key": "PROJ-1643", "started": "2026-10-19T09:00:00.000-0400", "seconds": 28800, "author_is_me": True},
                {"key": "PROJ-1643", "started": "2026-10-21T09:00:00.000-0400", "seconds": 7200, "author_is_me": True},
                {"key": "PROJ-1828", "started": "2026-10-20T09:00:00.000-0400", "seconds": 18000, "author_is_me": True},
                {"key": "PROJ-1828", "started": "2026-10-20T09:00:00.000-0400", "seconds": 3600, "author_is_me": False},
                {"key": "PROJ-1787", "started": "2026-10-16T09:00:00.000-0400", "seconds": 28800, "author_is_me": True}]
        _, d = self.write({"jira_worklogs": logs})
        h = d["jira_hours"]
        self.assertEqual((h["week"], h["target_h"], h["total_h"]), ("2026-W43", 40, 15.0))
        self.assertEqual((h["by_day"]["Mon"], h["by_day"]["Tue"], h["by_day"]["Wed"]), (8.0, 5.0, 2.0))
        self.assertEqual(h["by_ticket"], [{"key": "PROJ-1643", "hours": 10.0}, {"key": "PROJ-1828", "hours": 5.0}])

    def test_slack_truncated_and_validated(self):
        _, d = self.write({"slack": [{"kind": "dm", "who": "Alex", "text": "x " * 200, "url": "https://slack/1"}]})
        self.assertEqual(len(d["slack"][0]["text"]), 140)
        self.assertTrue(d["slack"][0]["text"].endswith("…"))
        r, _ = self.write({"slack": [{"kind": "channel", "url": "u"}]})
        self.assertEqual(r.returncode, 2)
        self.assertIn("slack kind", r.stderr)

    def test_bad_part_leaves_file_unchanged(self):
        self.write({"prs": [{"repo": "dbt", "number": 363}]})
        before = self.file.read_text()
        r, _ = self.write({"prs": [{"repo": "dbt", "number": "363"}]})
        self.assertEqual(r.returncode, 2)
        self.assertEqual(self.file.read_text(), before)

    def test_merge_keeps_other_sources_and_marks_errors(self):
        self.write({"prs": [{"repo": "dbt", "number": 363, "requested": "2026-10-07"}],
                    "slack": [{"kind": "mention", "url": "https://slack/2"}]}, now="2026-10-21T08:00:00Z")
        _, d = self.write({"calendar": [], "errors": {"prs": "Gmail search failed"}})
        self.assertEqual(d["prs"][0]["number"], 363)
        self.assertEqual(d["slack"][0]["kind"], "mention")
        self.assertEqual(d["sources"]["prs"], {"at": NOW, "ok": False, "note": "Gmail search failed",
                                               "data_at": "2026-10-21T08:00:00Z"})
        self.assertEqual(d["sources"]["slack"]["at"], "2026-10-21T08:00:00Z")

    def test_target_hours_kept(self):
        self.write({"jira_hours": {"week": "2026-W43", "target_h": 32, "total_h": 0, "by_day": {}, "by_ticket": []}})
        _, d = self.write({"jira_worklogs": []})
        self.assertEqual(d["jira_hours"]["target_h"], 32)

    def test_status_reports_age_and_stale(self):
        self.write({"slack": []}, now="2026-10-21T00:00:00Z")
        self.write({"calendar": []})
        out = self.run_tool("status").stdout
        self.assertIn("calendar    ok  0.0h old", out)
        self.assertIn("slack       ok  14.0h old (stale)", out)
        self.assertIn("prs         never", out)

    def test_unknown_error_source_rejected(self):
        r, _ = self.write({"errors": {"github": "x"}})
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()
