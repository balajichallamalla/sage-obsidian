#!/usr/bin/env python3
"""Tests for _system/tools/prep_context.py. Run: python3 -m unittest _system/tests/test_prep_context.py -v"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / "tools" / "prep_context.py"

PAGES = {
    "_system/config.json": '{"owner": {"first_name": "Jane", "match": ["jane"], "emails": ["jane.doe@example.com"]}}',
    "wiki/people/alex-morgan.md": "---\ntype: person\ntitle: Alex Morgan\naliases: [Alex]\n"
                                     "emails: [alex.morgan@example.com]\n---\n# Alex\n"
                                     "Works on [[nht-detection]] and [[data-watch-agent]].\n"
                                     "- [ ] On his page #todo/follow-up\n",
    "wiki/people/pat-kim.md": "---\ntype: person\ntitle: Pat Kim\naliases: [Pat]\nemails: []\n---\n"
                                   "Owns [[nht-detection]].\n",
    "wiki/people/yuki-sato.md": "---\ntype: person\ntitle: Yuki Sato\naliases: [YS, Yuki]\n"
                                    "emails: []\n---\n",
    "wiki/one-on-ones/1on1-alex-morgan.md": "---\ntype: one-on-one\ntitle: 1:1 Alex\n---\n"
                                               "## Open threads\n- Career goals.\n- Alerting build-out.\n"
                                               "## My commitments\n- [x] Old one #todo/growth\n"
                                               "- [ ] Share runbook #todo/follow-up 📅 2026-10-22\n"
                                               "## Their commitments\n- Refresh Northstar metrics.\n"
                                               "## Session history\n- 2026-09-30 — stuff.\n",
    "wiki/projects/nht-detection.md": "---\ntype: project\ntitle: NHT detection\n---\n",
    "wiki/projects/data-watch-agent.md": "---\ntype: project\ntitle: Data Watch agent\n---\n",
    "wiki/decisions/2026-10-16-direct-only.md": "---\ntype: decision\ntitle: Direct traffic only\n---\n",
    "wiki/tickets/PROJ-1.md": "---\ntype: ticket\ntitle: \"PROJ-1: patrick open\"\nkey: PROJ-1\n"
                              "status: In Progress\nassignee: \"[[pat-kim]]\"\n---\n",
    "wiki/tickets/PROJ-2.md": "---\ntype: ticket\ntitle: \"PROJ-2: patrick closed\"\nkey: PROJ-2\n"
                              "status: Closed\nassignee: \"[[pat-kim]]\"\n---\n",
    "wiki/tickets/PROJ-3.md": "---\ntype: ticket\ntitle: \"PROJ-3: mine\"\nkey: PROJ-3\n"
                              "status: In Progress\nassignee: Jane\n---\n",
    "wiki/meetings/2026-10-15-standup.md": "---\ntype: meeting\ntitle: Team – Platform Stand Up (2026-10-15)\n"
                                           "date: 2026-10-15\n---\n## Action items\n- [[pat-kim]]: old item\n",
    "wiki/meetings/2026-10-16-standup.md": "---\ntype: meeting\ntitle: Team – Platform Stand Up (2026-10-16)\n"
                                           "date: 2026-10-16\n---\n## Decisions\n- [[2026-10-16-direct-only]]\n"
                                           "## Action items\n- [[pat-kim]]: own the log pipeline\n"
                                           "- [[alex-morgan]]: share agreements\n## Related\n",
    "wiki/meetings/2026-10-20-standup.md": "---\ntype: meeting\ntitle: Team – Platform Stand Up (2026-10-20)\n"
                                           "date: 2026-10-20\n---\n## Action items\n- future\n",
    "wiki/projects/other.md": "---\ntype: project\ntitle: Other\n---\n- [ ] Ping [[pat-kim|Pat]] #todo/follow-up\n"
                              "- [x] Done ping [[pat-kim]] #todo/follow-up\n- [ ] Not about [[pat-kimx]] #todo/idea\n",
}


class PrepContextTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for relpath, text in PAGES.items():
            p = self.root / relpath
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def prep(self, title="Team - Platform Stand Up", emails="", date="2026-10-19"):
        env = dict(os.environ, VAULT_ROOT=str(self.root))
        r = subprocess.run([sys.executable, str(TOOL), "--title", title, "--emails", emails, "--date", date, "--json"],
                           env=env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    def test_email_match(self):
        c = self.prep(emails="alex.morgan@example.com")
        self.assertEqual(c["attendees"], [{"email": "alex.morgan@example.com", "slug": "alex-morgan",
                                           "name": "Alex Morgan"}])

    def test_alias_and_local_part_fallback(self):
        c = self.prep(emails="Yuki <ys@contractor.io>,pat.kim@example.com")
        self.assertEqual([a["slug"] for a in c["attendees"]], ["yuki-sato", "pat-kim"])

    def test_unmatched_and_self_excluded(self):
        c = self.prep(emails="Jane Doe <jane@x.com>,jane.doe@example.com")
        self.assertEqual(c["attendees"], [{"email": "jane@x.com", "slug": None, "name": "Jane Doe"}])
        self.assertEqual(c["people"], {})

    def test_open_todos_per_person(self):
        c = self.prep(emails="pat.kim@example.com,alex.morgan@example.com")
        self.assertEqual([t["text"][:4] for t in c["people"]["pat-kim"]["open_todos"]], ["Ping"])
        self.assertEqual(sorted(t["text"][:5] for t in c["people"]["alex-morgan"]["open_todos"]),
                         ["On hi", "Share"])

    def test_one_on_one_threads(self):
        o = self.prep(emails="alex.morgan@example.com")["people"]["alex-morgan"]["one_on_one"]
        self.assertEqual(o["open_threads"], ["Career goals.", "Alerting build-out."])
        self.assertEqual(o["my_commitments_open"], ["Share runbook #todo/follow-up 📅 2026-10-22"])
        self.assertEqual(o["their_commitments"], ["Refresh Northstar metrics."])
        self.assertIsNone(self.prep(emails="pat.kim@example.com")["people"]["pat-kim"]["one_on_one"])

    def test_tickets_in_progress_filter(self):
        t = self.prep(emails="pat.kim@example.com")["people"]["pat-kim"]["tickets_in_progress"]
        self.assertEqual([x["key"] for x in t], ["PROJ-1"])

    def test_recurring_latest_before_date(self):
        r = self.prep()["recurring"]
        self.assertEqual(r["date"], "2026-10-16")
        self.assertEqual(r["action_items"], ["[[pat-kim]]: own the log pipeline",
                                             "[[alex-morgan]]: share agreements"])
        self.assertEqual(self.prep(date="2026-10-16")["recurring"]["date"], "2026-10-15")
        self.assertIsNone(self.prep(title="Something else")["recurring"])

    def test_related_projects_and_decisions(self):
        c = self.prep(emails="alex.morgan@example.com,pat.kim@example.com")
        self.assertEqual([r["path"] for r in c["related"]][:2],
                         ["wiki/projects/nht-detection.md", "wiki/decisions/2026-10-16-direct-only.md"])
        self.assertIn("wiki/projects/data-watch-agent.md", [r["path"] for r in c["related"]])


if __name__ == "__main__":
    unittest.main()
