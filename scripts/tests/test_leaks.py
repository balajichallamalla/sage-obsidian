#!/usr/bin/env python3
"""No personal data in the template or in vaults rendered from it.

Generic patterns always run. Maintainers also get exact checks from scripts/dev/identity.local.json
("banned"), which is git-ignored.
"""
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "scripts"
IDENTITY = REPO / "scripts/dev/identity.local.json"
GENERIC = [
    (re.compile(r"\bU0(?!EXAMPLE\b|123456789\b)[A-Z0-9]{8,10}\b"), "Slack user ID"),
    (re.compile(r"\b\d{6}:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b"), "Atlassian account ID"),
    (re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b"), "UUID (cloud ID?)"),
    (re.compile(r"[\w.+-]+@xometry\.com"), "work email"),
]
ALLOWED = {"all_pdt@xometry.com"}  # Xometry-wide list, a preset default


def scan(root, recursive=True):
    banned = json.loads(IDENTITY.read_text())["banned"] if IDENTITY.is_file() else []
    hits = []
    for p in (root.rglob("*") if recursive else root.glob("*")):
        if not p.is_file() or ".git" in p.parts or p.suffix in {".png", ".jpg"}:
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        for rx, label in GENERIC:
            for m in rx.findall(text):
                if m not in ALLOWED:
                    hits.append(f"{p.relative_to(root)}: {label} {m}")
        for b in banned:
            if b in text:
                hits.append(f"{p.relative_to(root)}: banned string {b!r}")
    return hits


class LeakTest(unittest.TestCase):
    def test_template_skills_presets_clean(self):
        for d in ["template", "skills", "presets"]:
            with self.subTest(folder=d):
                self.assertEqual(scan(REPO / d), [])
        # user docs only; docs/specs and docs/plans are maintainer history and are not packaged
        self.assertEqual(scan(REPO / "docs", recursive=False), [])

    def test_rendered_vaults_clean(self):
        answers = {"owner": {"name": "Jane Doe", "email": "jane.doe@example.com"},
                   "sources": {"slack": {"user_id": "U0EXAMPLE"}, "jira": {"cloud_id": "cloud", "account_id": "acct"}}}
        with tempfile.TemporaryDirectory() as tmp:
            for preset in [p.stem for p in (REPO / "presets").glob("[!_]*.json")]:
                for mods in ({}, {"todoist": True}):
                    vault = Path(tmp) / f"{preset}-{len(mods)}"
                    a = json.loads(json.dumps(answers))
                    a["vault"] = {"name": "brain", "path": str(vault)}
                    a["modules"] = mods
                    (Path(tmp) / "a.json").write_text(json.dumps(a))
                    cfg = Path(tmp) / "c.json"
                    subprocess.run([sys.executable, str(SCRIPTS / "make_config.py"), "--preset", preset,
                                    "--answers", str(Path(tmp) / "a.json"), "--out", str(cfg)], check=True)
                    subprocess.run([sys.executable, str(SCRIPTS / "render_vault.py"), "--config", str(cfg),
                                    "--out", str(vault)], check=True, capture_output=True)
                    with self.subTest(vault=vault.name):
                        self.assertEqual(scan(vault), [])


if __name__ == "__main__":
    unittest.main()
