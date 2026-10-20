#!/usr/bin/env python3
"""Tests for _system/tools/search.py. Run: python3 -m unittest _system/tests/test_search.py -v"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / "tools" / "search.py"

PAGES = {
    "wiki/projects/nht-detection.md": "---\ntype: project\ntitle: NHT detection\naliases: [non-human traffic]\n"
                                      "tags: [bots]\ncreated: 2026-10-18\n---\n# NHT detection\nScores nht sessions.\n",
    "wiki/meetings/2026-10-14-grooming.md": "---\ntype: meeting\ntitle: Grooming\ndate: 2026-10-14\n"
                                           "attendees: [\"[[yuki-sato]]\"]\n---\n# Grooming\n"
                                           "We touched nht once.\n",
    "wiki/meetings/2026-09-30-standup.md": "---\ntype: meeting\ntitle: Standup\ndate: 2026-09-30\n---\n"
                                          "# Standup\nnht nht nht discussed again.\n",
    "wiki/people/yuki-sato.md": "---\ntype: person\ntitle: Yuki Sato\naliases: [YS, Yuki]\n---\n"
                                    "# Yuki Sato\nFrontend.\n",
    "wiki/concepts/coralogix.md": "---\ntype: concept\ntitle: Coralogix\naliases: []\n---\n# Coralogix\nLogs live here.\n",
    "raw/meetings/2026-10-14-grooming-raw.md": "nht nht nht nht nht nht raw transcript\n",
    "_system/normalize.md": "# x\n\n| Heard as | Write as |\n|---|---|\n| Core Logix | Coralogix |\n",
}


class SearchTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for rel, text in PAGES.items():
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def search(self, *args):
        env = dict(os.environ, VAULT_ROOT=str(self.root))
        r = subprocess.run([sys.executable, str(TOOL), *args, "--json"], env=env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    def paths(self, *args):
        return [h["path"] for h in self.search(*args)]

    def test_title_beats_body(self):
        self.assertEqual(self.paths("nht")[0], "wiki/projects/nht-detection.md")

    def test_type_and_date_filters(self):
        self.assertEqual(set(self.paths("nht", "--type", "meeting")),
                         {"wiki/meetings/2026-10-14-grooming.md", "wiki/meetings/2026-09-30-standup.md"})
        self.assertEqual(self.paths("nht", "--type", "meeting", "--since", "2026-10-01"),
                         ["wiki/meetings/2026-10-14-grooming.md"])
        self.assertEqual(self.paths("nht", "--until", "2026-09-30"), ["wiki/meetings/2026-09-30-standup.md"])

    def test_person_and_tag_filters(self):
        self.assertEqual(self.paths("nht", "--person", "yuki-sato"), ["wiki/meetings/2026-10-14-grooming.md"])
        self.assertEqual(self.paths("nht", "--tag", "bots"), ["wiki/projects/nht-detection.md"])

    def test_alias_and_normalize_expansion(self):
        self.assertEqual(self.paths("YS")[0], "wiki/people/yuki-sato.md")
        self.assertEqual(self.paths("core logix")[0], "wiki/concepts/coralogix.md")

    def test_raw_only_with_flag_and_weighted_down(self):
        self.assertNotIn("raw/meetings/2026-10-14-grooming-raw.md", self.paths("nht"))
        hits = self.paths("nht", "--raw")
        self.assertIn("raw/meetings/2026-10-14-grooming-raw.md", hits)
        self.assertEqual(hits[0], "wiki/projects/nht-detection.md")

    def test_linked_hub_outranks_short_title_match(self):
        pad = "Context line about modelling and sessions.\n" * 15
        hub = self.root / "wiki/projects/nht-detection.md"
        hub.write_text(hub.read_text() + pad, encoding="utf-8")
        (self.root / "wiki/decisions/2026-10-15-nht-rule.md").parent.mkdir(parents=True, exist_ok=True)
        (self.root / "wiki/decisions/2026-10-15-nht-rule.md").write_text(
            "---\ntype: decision\ntitle: NHT rule\n---\n# NHT rule\nOne nht rule.\n", encoding="utf-8")
        for i in range(10):
            (self.root / f"wiki/people/p{i}.md").write_text(f"# P{i}\nWorks on [[nht-detection]].\n", encoding="utf-8")
        self.assertEqual(self.paths("nht")[0], "wiki/projects/nht-detection.md")

    def test_json_fields_and_snippet(self):
        h = self.search("nht", "-n", "1")[0]
        self.assertEqual(set(h), {"rank", "path", "title", "date", "score", "snippet"})
        self.assertEqual((h["rank"], h["title"], h["date"]), (1, "NHT detection", "2026-10-18"))
        self.assertTrue(h["snippet"])


if __name__ == "__main__":
    unittest.main()
