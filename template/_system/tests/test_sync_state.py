#!/usr/bin/env python3
"""Tests for _system/tools/sync_state.py. Run: python3 -m unittest _system/tests/test_sync_state.py -v"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / "tools" / "sync_state.py"
NOW = "2026-10-18T12:00:00Z"


class SyncStateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state = Path(self.tmp.name) / "sync-state.json"
        self.env = dict(os.environ, SYNC_STATE=str(self.state), SYNC_NOW=NOW)
        self.state.write_text('{"backfill_start": "2026-08-26T00:00:00Z"}')

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args, now=None):
        env = dict(self.env)
        if now:
            env["SYNC_NOW"] = now
        return subprocess.run([sys.executable, str(TOOL), *args], env=env,
                              capture_output=True, text=True)

    def test_first_normal_window_is_last_7_days_and_stable(self):
        r = self.run_cli("window", "jira")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.split(), ["2026-10-11T12:00:00Z", NOW])
        r2 = self.run_cli("window", "jira", now="2026-10-18T13:00:00Z")
        self.assertEqual(r2.stdout.split(), ["2026-10-11T12:00:00Z", "2026-10-18T13:00:00Z"])

    def test_seen_mark_and_versions(self):
        self.assertEqual(self.run_cli("seen", "jira", "PROJ-1").returncode, 1)
        self.assertEqual(self.run_cli("mark", "jira", "PROJ-1", "wiki/tickets/PROJ-1.md",
                                      "--version", "2026-10-16T00:00:00Z").returncode, 0)
        self.assertEqual(self.run_cli("seen", "jira", "PROJ-1").returncode, 0)
        self.assertEqual(self.run_cli("seen", "jira", "PROJ-1", "--version",
                                      "2026-10-16T00:00:00Z").returncode, 0)
        self.assertEqual(self.run_cli("seen", "jira", "PROJ-1", "--version",
                                      "2026-10-17T00:00:00Z").returncode, 2)
        data = json.loads(self.state.read_text())
        self.assertEqual(data["sources"]["jira"]["seen"]["PROJ-1"]["path"], "wiki/tickets/PROJ-1.md")

    def test_advance_moves_normal_cursor_forward_only(self):
        self.run_cli("window", "slack")
        self.run_cli("advance", "slack", "2026-10-17T00:00:00Z")
        self.assertEqual(self.run_cli("window", "slack").stdout.split()[0], "2026-10-17T00:00:00Z")
        self.run_cli("advance", "slack", "2026-10-12T00:00:00Z")
        self.assertEqual(self.run_cli("window", "slack").stdout.split()[0], "2026-10-17T00:00:00Z")

    def test_backfill_weekly_windows_until_done(self):
        self.run_cli("window", "gmail")  # normal run first: backfill_end = 2026-10-11T12:00:00Z
        seen_windows = []
        for _ in range(20):
            out = self.run_cli("window", "gmail", "--backfill").stdout.split()
            if out == ["DONE"]:
                break
            seen_windows.append(out)
            self.run_cli("advance", "gmail", out[1], "--backfill")
        self.assertEqual(seen_windows[0], ["2026-08-26T00:00:00Z", "2026-09-02T00:00:00Z"])
        self.assertEqual(seen_windows[-1][1], "2026-10-11T12:00:00Z")
        self.assertEqual(len(seen_windows), 7)
        data = json.loads(self.state.read_text())
        self.assertTrue(data["sources"]["gmail"]["backfill_done"])

    def test_backfill_before_any_normal_run_sets_cursor(self):
        out = self.run_cli("window", "jira", "--backfill").stdout.split()
        self.assertEqual(out, ["2026-08-26T00:00:00Z", "2026-09-02T00:00:00Z"])
        self.assertEqual(self.run_cli("window", "jira").stdout.split()[0], "2026-10-11T12:00:00Z")

    def test_run_records_last_run(self):
        r = self.run_cli("run", "jira", "--status", "error", "--fetched", "0", "--new", "0",
                         "--updated", "0", "--note", "auth expired")
        self.assertEqual(r.returncode, 0, r.stderr)
        lr = json.loads(self.state.read_text())["sources"]["jira"]["last_run"]
        self.assertEqual((lr["status"], lr["note"], lr["at"]), ("error", "auth expired", NOW))

    def test_split_halves_window(self):
        r = self.run_cli("split", "2026-10-01T00:00:00Z", "2026-10-08T00:00:00Z")
        self.assertEqual(r.stdout.strip().splitlines(),
                         ["2026-10-01T00:00:00Z 2026-10-04T12:00:00Z",
                          "2026-10-04T12:00:00Z 2026-10-08T00:00:00Z"])

    def test_unknown_source_exits_3(self):
        self.assertEqual(self.run_cli("window", "twitter").returncode, 3)

    def test_status_lists_all_sources(self):
        out = self.run_cli("status").stdout
        for s in ["drive-meetings", "jira", "slack", "gmail", "github-prs", "claude-sessions"]:
            self.assertIn(s, out)


if __name__ == "__main__":
    unittest.main()
