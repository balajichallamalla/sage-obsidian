---
type: plan
title: sage-obsidian plugin — implementation plan
status: approved
created: 2026-10-20
updated: 2026-10-20
---
# sage-obsidian Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task, inline in the current session. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A shareable Claude plugin (`~/Desktop/Sage-obsidian`) that interviews a user, checks their connectors and builds a self-contained, customisable copy of Balaji's second-brain vault framework — with the same commands — plus doctor, upgrade and a neat README.

**Architecture:** `template/` is Balaji's vault framework made generic (placeholders `{{sage.*}}` + module blocks), produced by a repeatable import script. `scripts/make_config.py` merges presets + interview answers into `_system/config.json`; `scripts/render_vault.py` turns config + template into a vault (idempotent, module-aware, with a framework manifest for upgrades). Plugin skills: `setup`, `doctor`, `upgrade`, `help` and 12 thin routers into the vault's own workflows.

**Tech Stack:** Python 3 stdlib, Markdown skills (Claude plugin format: `.claude-plugin/plugin.json` + `marketplace.json`), Obsidian (Dataview, Tasks), Cowork/Claude Code connectors and scheduled tasks.

**Spec:** `docs/specs/2026-10-20-sage-obsidian-design.md`

## Global Constraints

- Repo root: `~/Desktop/Sage-obsidian` (Cowork bash: `/sessions/<session>/mnt/Sage-obsidian`). Balaji adds the GitHub remote and pushes; Claude never pushes.
- Generated vaults are local-only git: never add a remote.
- No top-level `bin/`. SKILL.md frontmatter keys ⊆ {name, description, license, compatibility, metadata, allowed-tools}; descriptions are JSON-quoted strings.
- Plugin name `sage-obsidian`; version `0.1.0`; `presets/_base.json` `plugin_version` matches.
- No personal data in `template/`, `skills/`, `presets/`, `docs/` or rendered vaults (leak test). Real identity strings live only in git-ignored `scripts/dev/identity.local.json`.
- Placeholders: `{{sage.<dotted.config.path>}}` only (Obsidian's `{{title}}` / `{{date:…}}` stay untouched). Module blocks: `<!-- module:X -->…<!-- /module -->`, `# module:X`…`# /module`, `// module:X`…`// /module`; `module:!X` = when off; `source:<name>` = sync on and that source enabled.
- Stdlib Python only. Cowork: when git leaves undeletable `*.lock`/`tmp_obj_*`, request delete permission for the folder, then clean `.git`.

---

## File Structure

| Path | Responsibility | Task |
|---|---|---|
| `scripts/render_vault.py`, `scripts/tests/test_render.py` | config + template → vault; update mode; manifest | 1 |
| `scripts/make_config.py`, `presets/*.json` | presets + answers → full config | 2 |
| `scripts/dev/import_vault.sh`, `scripts/dev/generalize_template.py`, `scripts/dev/identity.example.json`, `.gitignore` | repeatable template import from a working vault | 3 |
| `template/**` (hand-written: `modules.json`, `CLAUDE.md`, `_system/tests/check_vault.py`, `_system/tools/{vault_config,doctor}.py` + tests, seeds) | the generic vault framework | 3 |
| `scripts/tests/test_leaks.py` | no personal data anywhere shipped | 3 |
| `skills/**`, `scripts/dev/gen_router_skills.py`, `.claude-plugin/*.json`, `scripts/tests/test_packaging.py` | commands and packaging | 4 |
| `README.md`, `docs/*.md`, `CHANGELOG.md`, `LICENSE`, `migrations/README.md`, `scripts/package.sh` | docs and the Cowork zip | 5 |
| live install + `/setup` + `/doctor` | acceptance | 6 |

---

### Task 1: `render_vault.py` (TDD)

**Files:** Create `scripts/tests/test_render.py`, `scripts/render_vault.py`.

**Interfaces — Produces:** CLI `python3 scripts/render_vault.py --config C --out V [--update] [--template DIR] [--dry-run]` → prints `written: N` / `removed: N` / `kept: N` / `unchanged: N` (+ paths for written/removed); exit 2 with `render failed: …` on non-empty target (new mode), missing `_system/config.json` (update mode), unknown placeholder (`<file>: unknown placeholder {{sage.x}}`), unclosed block. Writes `V/_system/config.json` and `V/_system/.framework-manifest.json` (`{path: sha256}`, seeds excluded). `template/modules.json` = `{"files": {module: [fnmatch globs]}, "seed": [paths], "dirs": [paths]}`.

- [ ] **Step 1: Failing test** — `scripts/tests/test_render.py`:

~~~~python
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
~~~~

- [ ] **Step 2:** `python3 -m unittest scripts/tests/test_render.py -v` → all ERROR/FAIL (script missing).
- [ ] **Step 3: Implement** — `scripts/render_vault.py`:

~~~~python
#!/usr/bin/env python3
"""Render a sage-obsidian vault from a config file and the plugin's template.

Usage:
  render_vault.py --config CONFIG.json --out VAULT [--update] [--template DIR] [--dry-run]

New vault (default): VAULT must be missing or empty.
--update: re-render framework files in an existing vault (add/remove modules, upgrades); seed
          files that already exist and everything under raw/, wiki/, journal/ are left alone.
Writes _system/.framework-manifest.json (path -> sha256 of what was rendered) so /upgrade can tell
which framework files the user has edited.
Spec: docs/specs/2026-10-20-sage-obsidian-design.md §5–6. Stdlib only.
"""
import argparse
import fnmatch
import hashlib
import json
import re
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".md", ".py", ".js", ".css", ".json", ".base", ""}
PLACEHOLDER = re.compile(r"\{\{sage\.([A-Za-z0-9_.]+)\}\}")
START = re.compile(r"^\s*(?:<!--|#|//)\s*module:(!?)([\w:-]+)\s*(?:-->)?\s*$")
END = re.compile(r"^\s*(?:<!--|#|//)\s*/module\s*(?:-->)?\s*$")
MANIFEST = "_system/.framework-manifest.json"
PROTECTED = ("raw/", "wiki/", "journal/", "_system/state/")


class RenderError(Exception):
    pass


def lookup(config, dotted):
    cur = config
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            raise KeyError(dotted)
        cur = cur[part]
    if isinstance(cur, list):
        return ", ".join(str(x) for x in cur)
    if isinstance(cur, bool):
        return "true" if cur else "false"
    return str(cur)


def module_on(config, name):
    if name == "core":
        return True
    mods = config.get("modules", {})
    if name.startswith("source:"):
        src = name.split(":", 1)[1]
        return bool(mods.get("sync")) and bool(config.get("sources", {}).get(src, {}).get("enabled"))
    return bool(mods.get(name))


def apply_blocks(text, config, where):
    out, stack = [], []
    for n, line in enumerate(text.split("\n"), 1):
        m = START.match(line)
        if m:
            stack.append(module_on(config, m.group(2)) != bool(m.group(1)))
            continue
        if END.match(line):
            if not stack:
                raise RenderError(f"{where}:{n}: /module without a module start")
            stack.pop()
            continue
        if all(stack):
            out.append(line)
    if stack:
        raise RenderError(f"{where}: module block not closed")
    return "\n".join(out)


def fill(text, config, where):
    def sub(m):
        try:
            return lookup(config, m.group(1))
        except KeyError:
            raise RenderError(f"{where}: unknown placeholder {{{{sage.{m.group(1)}}}}}")
    return PLACEHOLDER.sub(sub, text)


def owner_of(rel, modules):
    for name, patterns in modules["files"].items():
        if any(fnmatch.fnmatch(rel, p) for p in patterns):
            return name
    return "core"


def plan(config, template):
    """Return {relative path: bytes} for every file the config should produce."""
    modules = json.loads((template / "modules.json").read_text(encoding="utf-8"))
    files = {}
    for p in sorted(template.rglob("*")):
        if not p.is_file() or p.name in ("modules.json", ".DS_Store") or "__pycache__" in p.parts:
            continue
        rel = p.relative_to(template).as_posix()
        if not module_on(config, owner_of(rel, modules)):
            continue
        data = p.read_bytes()
        if p.suffix in TEXT_SUFFIXES:
            text = fill(apply_blocks(data.decode("utf-8"), config, rel), config, rel)
            data = text.encode("utf-8")
        files[rel] = data
    for d in modules.get("dirs", []):
        files.setdefault(f"{d}/.gitkeep", b"")
    return files, modules


def sha(data):
    return hashlib.sha256(data).hexdigest()


def render(config, out, template, update=False, dry_run=False):
    files, modules = plan(config, template)
    seeds = set(modules.get("seed", []))
    if out.exists() and any(out.iterdir()) and not update:
        raise RenderError(f"{out} is not empty; use --update to change an existing vault")
    if update and not (out / "_system/config.json").is_file():
        raise RenderError(f"{out} has no _system/config.json; it is not a sage-obsidian vault")
    old = {}
    if update and (out / MANIFEST).is_file():
        old = json.loads((out / MANIFEST).read_text(encoding="utf-8"))
    changes = {"written": [], "unchanged": [], "kept": [], "removed": []}
    manifest = {}
    for rel, data in files.items():
        target = out / rel
        if update and rel in seeds and target.exists():
            changes["kept"].append(rel)
            continue
        if update and rel.startswith(PROTECTED) and not rel.endswith(".gitkeep") and target.exists():
            changes["kept"].append(rel)
            continue
        if rel not in seeds:
            manifest[rel] = sha(data)
        if target.exists() and target.read_bytes() == data:
            changes["unchanged"].append(rel)
            continue
        changes["written"].append(rel)
        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    for rel in sorted(set(old) - set(manifest)):
        target = out / rel
        if target.exists() and not rel.startswith(PROTECTED):
            changes["removed"].append(rel)
            if not dry_run:
                target.unlink()
    if not dry_run:
        (out / "_system").mkdir(parents=True, exist_ok=True)
        (out / "_system/config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
        (out / MANIFEST).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return changes


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--template", default=str(PLUGIN / "template"))
    ap.add_argument("--update", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    try:
        config = json.loads(Path(a.config).read_text(encoding="utf-8"))
        changes = render(config, Path(a.out).expanduser(), Path(a.template), a.update, a.dry_run)
    except (RenderError, json.JSONDecodeError, FileNotFoundError) as e:
        print(f"render failed: {e}", file=sys.stderr)
        return 2
    for k in ("written", "removed", "kept", "unchanged"):
        print(f"{k}: {len(changes[k])}")
        if k in ("written", "removed"):
            for rel in changes[k]:
                print(f"  {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
~~~~

- [ ] **Step 4:** `python3 -m unittest scripts/tests/test_render.py -v` → `Ran 10 tests … OK`.
- [ ] **Step 5: Commit** — `git add scripts && git commit -m "feat: render_vault.py — config + template → vault"`.

---

### Task 2: Presets and `make_config.py`

**Files:** Create `presets/_base.json`, `presets/{engineer,eng-manager,pm,data}.json`, `scripts/make_config.py`.

**Interfaces — Produces:** `python3 scripts/make_config.py --preset P --answers A.json [--out C.json]`; exit 2 `config failed: answers missing: …` when owner name/email or vault.path is missing. Fills `preset`, `setup_date`, `sync.backfill_start` (today − 8 weeks), `owner.first_name`, `owner.emails`, `owner.match`. Every `{{sage.*}}` key used by the template exists in `_base.json` (checked in Task 4).

- [ ] **Step 1:** `presets/_base.json`:

~~~~json
{
  "schema_version": 1,
  "plugin_version": "0.1.0",
  "setup_date": "",
  "preset": "",
  "owner": {"name": "", "first_name": "", "email": "", "emails": [], "match": [], "timezone": "America/New_York"},
  "vault": {"name": "second-brain", "path": ""},
  "modules": {"sync": true, "todoist": false, "schedules": true, "weekly": true, "prep": true, "dashboard": true},
  "sources": {
    "slack": {"enabled": true, "user_id": "", "channels": []},
    "jira": {"enabled": true, "site": "xometry.atlassian.net", "cloud_id": "", "account_id": "", "projects": []},
    "gmail": {"enabled": true, "exclude": "-to:all_pdt@xometry.com"},
    "drive_meetings": {"enabled": true, "folder": "Meet Recordings"},
    "github_prs": {"enabled": true, "org": "xometry", "repos": [], "review_channels": []},
    "claude_sessions": {"enabled": true}
  },
  "sync": {"backfill_start": ""},
  "todoist": {"project": "Work"},
  "schedules": {"morning": "30 8 * * 1-5", "end_of_day": "0 16 * * 1-5", "weekly": "0 15 * * 5"},
  "dashboard": {"hours_target": 40, "stale_hours": 12},
  "todo_categories": ["project", "follow-up", "review", "ticket", "idea", "growth"]
}
~~~~

`presets/engineer.json`:

~~~~json
{"label": "Engineer", "description": "Tickets, PRs and repos front and centre; standups and 1:1s.",
 "modules": {"sync": true, "todoist": false, "schedules": true, "weekly": true, "prep": true, "dashboard": true},
 "sources": {"slack": {"enabled": true}, "jira": {"enabled": true}, "gmail": {"enabled": false},
             "drive_meetings": {"enabled": true}, "github_prs": {"enabled": true}, "claude_sessions": {"enabled": true}}}
~~~~

`presets/eng-manager.json`:

~~~~json
{"label": "Eng manager", "description": "1:1s, team decisions, weekly impact for reviews; email and meeting notes on.",
 "modules": {"sync": true, "todoist": true, "schedules": true, "weekly": true, "prep": true, "dashboard": true},
 "sources": {"slack": {"enabled": true}, "jira": {"enabled": true}, "gmail": {"enabled": true},
             "drive_meetings": {"enabled": true}, "github_prs": {"enabled": false}, "claude_sessions": {"enabled": false}}}
~~~~

`presets/pm.json`:

~~~~json
{"label": "PM", "description": "Meetings, decisions, stakeholders and email; tickets without PRs.",
 "modules": {"sync": true, "todoist": true, "schedules": true, "weekly": true, "prep": true, "dashboard": true},
 "sources": {"slack": {"enabled": true}, "jira": {"enabled": true}, "gmail": {"enabled": true},
             "drive_meetings": {"enabled": true}, "github_prs": {"enabled": false}, "claude_sessions": {"enabled": false}}}
~~~~

`presets/data.json`:

~~~~json
{"label": "Data / analytics", "description": "Analyses, tickets, PRs to dbt-style repos, Claude research sessions.",
 "modules": {"sync": true, "todoist": false, "schedules": true, "weekly": true, "prep": true, "dashboard": true},
 "sources": {"slack": {"enabled": true}, "jira": {"enabled": true}, "gmail": {"enabled": false},
             "drive_meetings": {"enabled": true}, "github_prs": {"enabled": true}, "claude_sessions": {"enabled": true}}}
~~~~

- [ ] **Step 2:** `scripts/make_config.py`:

~~~~python
#!/usr/bin/env python3
"""Build a full config.json from presets/_base.json + a role preset + the setup answers.

Usage: make_config.py --preset engineer --answers answers.json [--out config.json]
answers.json holds only what the interview collected (owner, vault, modules, sources, ...);
anything missing falls back to the preset, then to _base.json. Prints the config if --out is omitted.
"""
import argparse
import copy
import datetime as dt
import json
import sys
from pathlib import Path

PRESETS = Path(__file__).resolve().parents[1] / "presets"


def merge(base, over):
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        out[k] = merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else copy.deepcopy(v)
    return out


def build(preset, answers, today=None):
    base = json.loads((PRESETS / "_base.json").read_text(encoding="utf-8"))
    p = json.loads((PRESETS / f"{preset}.json").read_text(encoding="utf-8"))
    p = {k: v for k, v in p.items() if k not in ("label", "description")}
    cfg = merge(merge(base, p), answers)
    today = today or dt.date.today()
    cfg["preset"] = preset
    cfg["setup_date"] = cfg.get("setup_date") or today.isoformat()
    if not cfg["sync"].get("backfill_start"):
        cfg["sync"]["backfill_start"] = (today - dt.timedelta(weeks=8)).isoformat()
    o = cfg["owner"]
    if not o.get("first_name") and o.get("name"):
        o["first_name"] = o["name"].split()[0]
    if o.get("email") and o["email"] not in o["emails"]:
        o["emails"] = [o["email"]] + o["emails"]
    if not o.get("match"):
        o["match"] = sorted({x.lower() for x in [o.get("first_name", ""), o.get("name", "")] + o["emails"] if x})
    missing = [k for k in ("name", "email") if not o.get(k)] + ([] if cfg["vault"].get("path") else ["vault.path"])
    if missing:
        raise ValueError(f"answers missing: {', '.join(missing)}")
    return cfg


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--preset", required=True, choices=sorted(p.stem for p in PRESETS.glob("[!_]*.json")))
    ap.add_argument("--answers", required=True)
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    try:
        cfg = build(a.preset, json.loads(Path(a.answers).read_text(encoding="utf-8")))
    except ValueError as e:
        print(f"config failed: {e}", file=sys.stderr)
        return 2
    text = json.dumps(cfg, indent=2) + "\n"
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
~~~~

- [ ] **Step 3: Check** — `echo '{"owner":{"name":"Jane Doe","email":"jane@example.com"},"vault":{"path":"/tmp/v"}}' > /tmp/a.json && python3 scripts/make_config.py --preset engineer --answers /tmp/a.json | head -5` → JSON with `"preset": "engineer"`; and with `{}` answers → exit 2 `answers missing: name, email, vault.path`.
- [ ] **Step 4: Commit** — `git add presets scripts/make_config.py && git commit -m "feat: presets and make_config.py"`.

---

### Task 3: Generic template + leak test

**Files:** Create `.gitignore`, `scripts/dev/{import_vault.sh,generalize_template.py,identity.example.json}`, git-ignored `scripts/dev/identity.local.json`, hand-written template files, `scripts/tests/test_leaks.py`; generated `template/**`.

**Interfaces:** Consumes Tasks 1–2. Produces `template/` whose rendered vaults pass their own `check_vault.py` and tool tests for every preset, all-on and minimal.

- [ ] **Step 1: Failing leak test** — `scripts/tests/test_leaks.py`:

~~~~python
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


def scan(root):
    banned = json.loads(IDENTITY.read_text())["banned"] if IDENTITY.is_file() else []
    hits = []
    for p in root.rglob("*"):
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
        for d in ["template", "skills", "presets", "docs"]:
            if (REPO / d).is_dir():
                with self.subTest(folder=d):
                    self.assertEqual(scan(REPO / d), [])

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
~~~~

`python3 -m unittest scripts/tests/test_leaks.py` → ERROR (no `template/modules.json`).

- [ ] **Step 2: Import tooling** — `.gitignore`:

~~~~
scripts/dev/identity.local.json
dist/
__pycache__/
.DS_Store
~~~~

`scripts/dev/import_vault.sh` (chmod +x):

~~~~bash
#!/usr/bin/env bash
# Copy the framework (never content) from a working vault into template/, then generalize it.
# Usage: scripts/dev/import_vault.sh ~/Desktop/second-brain
set -euo pipefail
V="${1:?vault path}"; T="$(cd "$(dirname "$0")/../.." && pwd)/template"
keep=(modules.json CLAUDE.md _system/tests/check_vault.py _system/tools/vault_config.py
      _system/tools/doctor.py _system/tests/test_vault_config.py _system/tests/test_doctor.py index.md log.md inbox.md
      _system/normalize.md)
stash="$(mktemp -d)"; for f in "${keep[@]}"; do [ -e "$T/$f" ] && mkdir -p "$stash/$(dirname "$f")" && cp "$T/$f" "$stash/$f"; done
rm -rf "$T"; mkdir -p "$T"
for f in todos.md home.md .gitignore _system/HELP.md _system/SETUP.md .obsidian/app.json .obsidian/appearance.json .obsidian/core-plugins.json \
         .obsidian/community-plugins.json .obsidian/daily-notes.json .obsidian/graph.json .obsidian/templates.json \
         .obsidian/plugins/dataview/data.json; do mkdir -p "$T/$(dirname "$f")"; cp "$V/$f" "$T/$f"; done
for d in workflows page-types templates sources tools tests dashboard; do mkdir -p "$T/_system/$d"; cp -R "$V/_system/$d/." "$T/_system/$d/"; done
find "$T" -name __pycache__ -prune -exec rm -rf {} + ; find "$T" -name .DS_Store -delete
python3 "$(dirname "$0")/generalize_template.py" "$T"
cp -R "$stash/." "$T/"; rm -rf "$stash"
echo "template imported from $V (hand-written files kept: ${keep[*]})"
~~~~

`scripts/dev/generalize_template.py`:

~~~~python
#!/usr/bin/env python3
"""Turn a fresh copy of Balaji's vault framework (template/) into the generic sage-obsidian template.

Needs scripts/dev/identity.local.json (git-ignored; see identity.example.json).
Usage (from the repo root, after scripts/dev/import_vault.sh):
  python3 scripts/dev/generalize_template.py template
Every edit asserts it matched exactly once, so a changed source vault fails loudly instead of
shipping half-generalised files.
"""
import json
import re
import sys
from pathlib import Path

T = Path(sys.argv[1] if len(sys.argv) > 1 else "template")
TEXT = {".md", ".py", ".js", ".css", ".json", ""}


def files(pattern="**/*"):
    return [p for p in sorted(T.glob(pattern)) if p.is_file() and p.suffix in TEXT]


def edit(rel, *pairs):
    p = T / rel
    s = p.read_text(encoding="utf-8")
    for old, new in pairs:
        n = len(old.findall(s)) if isinstance(old, re.Pattern) else s.count(old)
        assert n == 1, f"{rel}: expected 1 match, found {n}: {getattr(old, 'pattern', old)[:70]!r}"
        s = old.sub(new, s) if isinstance(old, re.Pattern) else s.replace(old, new)
    p.write_text(s, encoding="utf-8")


def replace_all(paths, table):
    for p in paths:
        s = p.read_text(encoding="utf-8")
        for old, new in table:
            s = s.replace(old, new)
        p.write_text(s, encoding="utf-8")


# 1. IDs and identity everywhere except tests (tests get fake people in step 4)
IDENTITY = json.loads((Path(__file__).parent / "identity.local.json").read_text(encoding="utf-8"))
IDS = [tuple(x) for x in IDENTITY["replace"]]  # real IDs / names -> {{sage.*}} placeholders
non_tests = [p for p in files() if "_system/tests" not in p.as_posix()
             and p.suffix != ".json" and not p.as_posix().endswith(".js")]
replace_all(non_tests, IDS)

# 2. Source specs: org, repos, channels, ticket keys
edit("_system/sources/github-prs.md",
     ("`[xometry/<repo>] <title> (PR #<n>)`", "`[{{sage.sources.github_prs.org}}/<repo>] <title> (PR #<n>)`"),
     ("--author @me --owner xometry", "--author @me --owner {{sage.sources.github_prs.org}}"),
     ("--review-requested @me --owner xometry", "--review-requested @me --owner {{sage.sources.github_prs.org}}"),
     ("-R xometry/<repo>", "-R {{sage.sources.github_prs.org}}/<repo>"),
     ("`https://github.com/xometry/<repo>/pull/<n>`", "`https://github.com/{{sage.sources.github_prs.org}}/<repo>/pull/<n>`"),
     ("`url: https://github.com/xometry/<repo>`", "`url: https://github.com/{{sage.sources.github_prs.org}}/<repo>`"),
     (re.compile(r"^- Owner `xometry` only\..*$", re.M),
      "- Owner `{{sage.sources.github_prs.org}}` only. Keep PRs authored by {{sage.owner.first_name}} or with "
      "{{sage.owner.first_name}}'s review requested. If the repo allowlist (`{{sage.sources.github_prs.repos}}`) "
      "is not empty, also require the repo to be on it **or** the title/branch to mention a ticket key from "
      "`{{sage.sources.jira.projects}}`."),
     (re.compile(r"^- Narrow discovery with .*$", re.M),
      "- If discovery overflows (more than ~40 PRs/week), narrow the Gmail query with the allowlisted "
      "repo names and ticket keys."))
edit("_system/sources/gmail.md", ("-to:all_pdt@xometry.com", "{{sage.sources.gmail.exclude}}"))
edit("_system/sources/claude-sessions.md", ("(`MKTM-1797`) → link `[[MKTM-1797]]`", "(`PROJ-123`) → link `[[PROJ-123]]`"))
edit("_system/workflows/dash.md",
     ("review-request messages in\n   #martech-reviews.",
      "review-request messages in\n   {{sage.sources.github_prs.review_channels}} (skip if none are configured)."))
edit("_system/workflows/weekly.md",
     (re.compile(r"Run steps 2–4 for every week from `2026-W35` \(week of 2026-08-26\)"),
      "Run steps 2–4 for every week from the ISO week of `{{sage.sync.backfill_start}}`"),
     (re.compile(r"Seed the impact log with these past wins.*?(?=\n\n)", re.S),
      "Ask {{sage.owner.first_name}} for 3–6 past wins worth seeding (find each page with `search.py`; "
      "skip any already present) and add them as `(auto)` lines."))
edit("_system/workflows/schedule.md",
     (re.compile(r"Two Cowork scheduled tasks run the vault on weekdays"),
      "Cowork scheduled tasks run the vault"))
edit("_system/HELP.md",
     ("`/prep standup` · `/prep Tyler`", "`/prep standup` · `/prep <name>`"),
     ("one week per run from 2026-08-26", "one week per run from {{sage.sync.backfill_start}}"),
     (re.compile(r"Claude Code commands start with `/`\..*?\n(?=\n## Commands)", re.S),
      "Commands come from the **sage-obsidian** plugin. In Claude Code type `/sage-obsidian:<command>`\n"
      "(e.g. `/sage-obsidian:sync`); in Cowork pick the skill or just ask (\"run sync\").\n"
      "This guide writes them short, as `/sync`.\n"),
     ("| `/vault-help [topic]` | This guide, or one section of it | `/vault-help recipes` |",
      "| `/help [topic]` | This guide, or one section of it | `/help recipes` |"))

# 3. Tools read the owner from _system/config.json
edit("_system/tools/week_facts.py",
     ("from search import parse_fm, split_fm, as_list  # noqa: E402\n",
      "from search import parse_fm, split_fm, as_list  # noqa: E402\nfrom vault_config import is_owner  # noqa: E402\n"),
     ('ME = "balaji"\n', ""),
     ('        if ME in str(fm.get("assignee", "")).lower() and not is_closed(status):',
      '        if is_owner(fm.get("assignee", "")) and not is_closed(status):'),
     ('        if ME in str(pr["author"]).lower():', '        if is_owner(pr["author"]):'),
     ('        if ME in str(t["assignee"]).lower():', '        if is_owner(t["assignee"]):'))
edit("_system/tools/prep_context.py",
     ("from week_facts import BOX_RE", "from vault_config import owner_emails  # noqa: E402\nfrom week_facts import BOX_RE"),
     ('ME_EMAILS = {"{{sage.owner.email}}"}\n', ""),
     ('    return [a for a in out if a["email"] not in ME_EMAILS]', '    return [a for a in out if a["email"] not in owner_emails()]'))
edit("_system/tools/sync_state.py",
     ('BACKFILL_START = "2026-08-26T00:00:00Z"', 'BACKFILL_START = "{{sage.sync.backfill_start}}T00:00:00Z"'))
edit("_system/tools/gen_page_types.py", ("e.g. {{sage.sources.slack.user_id}}", "e.g. U0123456789"))
edit("_system/page-types/person.md", ("e.g. {{sage.sources.slack.user_id}}", "e.g. U0123456789"))
edit("_system/dashboard/command-center/view.js",
     ('const ME = "balaji";\n', ""),
     ("const snap = (await loadJson(", "const cfg = (await loadJson(\"_system/config.json\")) || {};\n"
      "const ME = ((cfg.owner && cfg.owner.match) || [(cfg.owner && cfg.owner.first_name) || \"\"]).map(s => String(s).toLowerCase()).filter(Boolean);\n"
      "const FIRST = (cfg.owner && cfg.owner.first_name) || \"there\";\n"
      "const snap = (await loadJson("),
     ("const isMine = v => lower(v).includes(ME);", "const isMine = v => ME.some(m => lower(v).includes(m));"),
     ('"evening"}, Balaji`', '"evening"}, ${FIRST}`'),
     ("if (!x || x[1].includes(ME) || shown >= 6) continue;", "if (!x || isMine(x[1]) || shown >= 6) continue;"))

# 4. Test fixtures: fake people, fake project key, config file for the owner
FAKE = [tuple(x) for x in IDENTITY["fixtures"]]  # real people in test fixtures -> fake ones
replace_all(files("_system/tests/test_*.py"), FAKE)
CONFIG_FIXTURE = ('    "_system/config.json": \'{"owner": {"first_name": "Jane", "match": ["jane"], '
                  '"emails": ["jane.doe@example.com"]}}\',\n')
edit("_system/tests/test_sync_state.py",
     ("        self.env = dict(os.environ, SYNC_STATE=str(self.state), SYNC_NOW=NOW)\n",
      "        self.env = dict(os.environ, SYNC_STATE=str(self.state), SYNC_NOW=NOW)\n"
      "        self.state.write_text('{\"backfill_start\": \"2026-08-26T00:00:00Z\"}')\n"))
for rel in ["_system/tests/test_week_facts.py", "_system/tests/test_prep_context.py"]:
    edit(rel, (re.compile(r"^PAGES = \{\n", re.M), "PAGES = {\n" + CONFIG_FIXTURE))
# 5. Module blocks in imported markdown
def wrap_line(rel, prefix, module):
    lines = (T / rel).read_text(encoding="utf-8").split("\n")
    hits = [i for i, l in enumerate(lines) if l.startswith(prefix)]
    assert len(hits) == 1, f"{rel}: {prefix!r} matched {len(hits)} lines"
    i = hits[0]
    lines[i:i + 1] = [f"<!-- module:{module} -->", lines[i], "<!-- /module -->"]
    (T / rel).write_text("\n".join(lines), encoding="utf-8")


def wrap_section(rel, heading, module):
    lines = (T / rel).read_text(encoding="utf-8").split("\n")
    hits = [i for i, l in enumerate(lines) if l.strip() == heading]
    assert len(hits) == 1, f"{rel}: heading {heading!r} matched {len(hits)}"
    i = hits[0]
    level = heading.split(" ")[0]
    j = i + 1
    while j < len(lines) and not (lines[j].startswith("#") and len(lines[j].split(" ")[0]) <= len(level)
                                  and lines[j].split(" ")[0].strip("#") == ""):
        j += 1
    lines[i:j] = [f"<!-- module:{module} -->"] + lines[i:j] + ["<!-- /module -->"]
    (T / rel).write_text("\n".join(lines), encoding="utf-8")


for prefix, module in [("| `/sync [", "sync"), ("| `/sync-status`", "sync"), ("| `/todo-sync`", "todoist"),
                       ("| `/weekly", "weekly"), ("| `/prep", "prep"), ("| `/dash`", "dashboard"),
                       ("| Drive meeting notes", "sync"), ("| Gmail", "sync"), ("| Jira, PRs, Slack", "sync")]:
    wrap_line("_system/HELP.md", prefix, module)
for heading, module in [("### Daily sync", "sync"), ("### First run", "sync"), ("### Scheduled runs", "schedules"),
                        ("### Weekly", "weekly"), ("### Prep for a 1:1 with someone", "prep"),
                        ("### Meeting prep", "prep"), ("### Command center", "dashboard")]:
    wrap_section("_system/HELP.md", heading, module)
wrap_line("_system/workflows/sync.md", "8. **To-dos.**", "todoist")
wrap_line("_system/workflows/daily.md", "8. Run `_system/workflows/todo-sync.md`", "todoist")
def wrap_item(rel, prefix, module):
    lines = (T / rel).read_text(encoding="utf-8").split("\n")
    hits = [i for i, l in enumerate(lines) if l.startswith(prefix)]
    assert len(hits) == 1, f"{rel}: {prefix!r} matched {len(hits)}"
    i = j = hits[0]
    j += 1
    while j < len(lines) and not re.match(r"^\d+\. |^## ", lines[j]):
        j += 1
    lines[i:j] = [f"<!-- module:{module} -->"] + lines[i:j] + ["<!-- /module -->"]
    (T / rel).write_text("\n".join(lines), encoding="utf-8")


for prefix, module in [("2. **jira_worklogs**", "source:jira"), ("3. **slack**", "source:slack"),
                       ("4. **prs**", "source:github_prs")]:
    wrap_item("_system/workflows/dash.md", prefix, module)
print("module blocks added")
print("generalized", T)
~~~~

`scripts/dev/identity.example.json`:

~~~~json
{
  "_comment": "Copy to identity.local.json and fill with the source vault owner's real strings.",
  "replace": [
    [
      "<real cloudId>",
      "{{sage.sources.jira.cloud_id}}"
    ],
    [
      "<real Jira accountId>",
      "{{sage.sources.jira.account_id}}"
    ],
    [
      "<real Slack user ID>",
      "{{sage.sources.slack.user_id}}"
    ],
    [
      "<real email>",
      "{{sage.owner.email}}"
    ],
    [
      "<First name>'s",
      "{{sage.owner.first_name}}'s"
    ],
    [
      "<First name>",
      "{{sage.owner.first_name}}"
    ]
  ],
  "fixtures": [
    [
      "<colleague-slug>",
      "alex-morgan"
    ],
    [
      "<PROJECTKEY>",
      "PROJ"
    ]
  ],
  "banned": [
    "<strings that must never appear in the template or rendered vaults>"
  ]
}
~~~~

Create `scripts/dev/identity.local.json` (git-ignored) from the example with Balaji's real values: the `replace` pairs (cloudId, Jira accountId, Slack user ID, work email, Jira host strings, timezone, first name), the `fixtures` pairs (colleague names/slugs/emails → fake ones, project key → PROJ, team names), and `banned` (name, surname, IDs, Todoist ID prefix, colleague names, `MKTM-1`, team slug). Never commit it; never print its contents into the plan or docs.

- [ ] **Step 3: Hand-written template files** (kept across re-imports):

`template/modules.json`:

~~~~json
{
  "files": {
    "sync": ["_system/workflows/sync.md", "_system/workflows/sync-status.md", "_system/tools/sync_state.py",
             "_system/tests/test_sync_state.py"],
    "source:slack": ["_system/sources/slack.md", "_system/workflows/ingest-slack.md"],
    "source:jira": ["_system/sources/jira.md", "_system/workflows/ingest-jira.md"],
    "source:gmail": ["_system/sources/gmail.md", "_system/workflows/ingest-email.md"],
    "source:drive_meetings": ["_system/sources/drive-meetings.md", "_system/workflows/ingest-drive.md"],
    "source:github_prs": ["_system/sources/github-prs.md", "_system/workflows/ingest-pr.md"],
    "source:claude_sessions": ["_system/sources/claude-sessions.md", "_system/workflows/ingest-claude-session.md"],
    "todoist": ["_system/workflows/todo-sync.md", "_system/tools/todo_sync.py", "_system/tests/test_todo_sync.py"],
    "schedules": ["_system/workflows/schedule.md"],
    "weekly": ["_system/workflows/weekly.md"],
    "prep": ["_system/workflows/prep.md", "_system/tools/prep_context.py", "_system/tests/test_prep_context.py"],
    "dashboard": ["home.md", "_system/dashboard/*", "_system/workflows/dash.md", "_system/tools/dash_snapshot.py",
                  "_system/tests/test_dash_snapshot.py"]
  },
  "seed": ["index.md", "log.md", "inbox.md", "_system/normalize.md"],
  "dirs": ["raw/meetings", "raw/one-on-ones", "raw/slack", "raw/email", "raw/claude-sessions", "raw/thoughts",
           "raw/clips", "raw/assets", "wiki/people", "wiki/projects", "wiki/repos", "wiki/tickets", "wiki/prs",
           "wiki/meetings", "wiki/one-on-ones", "wiki/concepts", "wiki/ideas", "wiki/decisions", "wiki/syntheses",
           "wiki/weekly", "journal", "_system/state/digests"]
}
~~~~

`template/CLAUDE.md`:

~~~~markdown
# Second Brain — LLM Wiki schema

This is {{sage.owner.first_name}}'s personal work knowledge base, built on Andrej Karpathy's "LLM Wiki" pattern.
You (Claude) are the wiki's maintainer. {{sage.owner.first_name}} curates sources and asks questions; you do the
summarising, cross-referencing, filing, and bookkeeping. Obsidian is the IDE, you are the
programmer, the wiki is the codebase.

Commands come from the **sage-obsidian** plugin (`/sage-obsidian:<name>` in Claude Code).
Settings live in `_system/config.json` — re-run setup to change modules or sources.

## Three layers

1. **`raw/`** — immutable source captures (meeting notes, 1:1s, Slack threads, Claude sessions,
   thoughts, clips). Source of truth. You read it; you never edit it after capture.
2. **`wiki/`** — pages you write and maintain, one folder per entity type.
3. **Schema** — this file plus `_system/` (workflows, page types, templates).

## Folder map

| Path | What lives there |
|---|---|
| `index.md` | Catalog of every wiki page, by type. Read it first for any question. |
| `log.md` | Append-only history: `## [YYYY-MM-DD] <op> | <title>` |
| `inbox.md` | Quick captures waiting for `/inbox` triage |
| `todos.md` | Live Tasks-plugin view of open checkboxes (do not hand-edit queries) |
<!-- module:dashboard -->
| `home.md` | Command center (DataviewJS view in `_system/dashboard/`; connector snapshot via `/dash`) |
<!-- /module -->
| `journal/` | `YYYY-MM-DD.md` daily pages |
| `raw/{meetings,one-on-ones,slack,email,claude-sessions,thoughts,clips,assets}/` | Captures (files end in `-raw.md`) |
| `wiki/{people,projects,repos,tickets,prs,meetings,one-on-ones,concepts,ideas,decisions,syntheses,weekly}/` | Entity pages |
| `_system/page-types/<type>.md` | Frontmatter + body spec per type — follow exactly |
| `_system/templates/` | Obsidian templates (same shapes as page types) |
| `_system/workflows/` | Step-by-step procedures (routing table below) |
| `_system/sources/` · `_system/state/` | Connector source specs · sync cursors and digests |
| `_system/HELP.md` | User-facing command guide |

## Golden rules

1. Never modify files in `raw/` after capture. New info → new raw file.
2. Every operation appends to `log.md`. Every created or renamed wiki page updates `index.md`.
3. Every claim on a wiki page must trace to an entry in its `sources:` frontmatter.
4. Contradictions: add a `> [!warning] Conflict` callout on both pages linking both sources.
   Never silently overwrite an older claim.
5. Before creating a person/project/repo page, search existing `aliases` for a match.
   If unsure whether two names are the same entity, ask.
6. Use `[[wikilinks]]` for every person, project, repo, ticket, and PR mention — even if the
   page does not exist yet.
7. Finish each completed operation with exactly one git commit:
   `<op>(<type>): <title>` (e.g. `ingest(meeting): 2026-10-18 platform sync`).
   This repo is local only — never run `git remote add` or push. No git remote, ever.
8. Never write secrets, credentials, passwords, compensation/salary figures, health details,
   or customer PII into the vault. If a source contains them, keep the raw file, exclude the
   content from the wiki, and note "sensitive content excluded" in the log (without quoting).
9. Update `updated:` on every page you touch. Dates are `YYYY-MM-DD`.
10. If a request needs a module that is off (see `_system/config.json` → `modules`), say which one
    and that re-running setup (`/sage-obsidian:setup`) turns it on.
11. Sync state in `_system/state/sync-state.json` changes only through
    `_system/tools/sync_state.py` or `_system/tools/todo_sync.py`, and only in the same commit
    as the content it covers.
12. When writing wiki pages, apply `_system/normalize.md` corrections (never to `raw/`).

## File naming

- Lowercase hyphenated slugs: `wiki/people/jane-doe.md`, `wiki/projects/quote-engine-v2.md`.
- Tickets keep the Jira key: `wiki/tickets/XOM-1234.md`. PRs: `wiki/prs/<repo>-<number>.md`.
- 1:1 running pages: `wiki/one-on-ones/1on1-<person-slug>.md` (prefix avoids a basename clash
  with `wiki/people/<person-slug>.md`, which would make `[[person-slug]]` links ambiguous).
- Dated pages: `YYYY-MM-DD-<slug>.md` (meetings, decisions, raw captures).
- Raw captures end in `-raw` (`raw/meetings/2026-10-16-standup-raw.md`); re-captures `-raw-v2`.

## To-dos

{{sage.owner.first_name}}'s own to-dos are checkboxes with one category tag:
`- [ ] Send rollout plan to [[jane-doe]] #todo/follow-up 📅 2026-10-22`
Categories: `#todo/project` (+ project slug tag), `#todo/follow-up`, `#todo/review`,
`#todo/ticket`, `#todo/idea`, `#todo/growth`. Other people's action items are plain bullets
with `[[owner]]` — no checkbox. `🆔 td:<id>` is written only by `todo-sync`.

## Routing — which workflow to read

| Request | Read and follow |
|---|---|
| `/ingest`, "file this", "add this to the vault" | `_system/workflows/ingest.md` (routes to the right one below) |
| Meeting notes / transcript | `_system/workflows/ingest-meeting.md` |
| 1:1 notes | `_system/workflows/ingest-1on1.md` |
| A thought, idea, brain dump | `_system/workflows/ingest-thought.md` |
| Article / doc in `raw/clips/` | `_system/workflows/ingest-clip.md` |
<!-- module:source:drive_meetings -->
| Google Drive doc / Gemini notes link | `_system/workflows/ingest-drive.md` |
<!-- /module -->
<!-- module:source:jira -->
| Jira key or URL | `_system/workflows/ingest-jira.md` |
<!-- /module -->
<!-- module:source:slack -->
| Slack permalink | `_system/workflows/ingest-slack.md` |
<!-- /module -->
<!-- module:source:gmail -->
| Gmail thread | `_system/workflows/ingest-email.md` |
<!-- /module -->
<!-- module:source:github_prs -->
| GitHub PR URL | `_system/workflows/ingest-pr.md` |
<!-- /module -->
<!-- module:source:claude_sessions -->
| Claude session | `_system/workflows/ingest-claude-session.md` |
<!-- /module -->
<!-- module:sync -->
| `/sync [sources] [--backfill]` | `_system/workflows/sync.md` |
<!-- /module -->
<!-- module:sync -->
| `/sync-status` | `_system/workflows/sync-status.md` |
<!-- /module -->
| `/ask` or any question about the vault's content | `_system/workflows/query.md` |
| `/lint`, "health check" | `_system/workflows/lint.md` |
| `/inbox` | `_system/workflows/inbox.md` |
| `/daily`, "end of day" | `_system/workflows/daily.md` |
<!-- module:todoist -->
| `/todo-sync`, Todoist sync | `_system/workflows/todo-sync.md` |
<!-- /module -->
| `/search` | `_system/workflows/search.md` |
<!-- module:weekly -->
| `/weekly [week] [--backfill]` | `_system/workflows/weekly.md` |
<!-- /module -->
<!-- module:prep -->
| `/prep <meeting or person>`, morning prep | `_system/workflows/prep.md` |
<!-- /module -->
<!-- module:dashboard -->
| `/dash`, refresh the dashboard | `_system/workflows/dash.md` |
<!-- /module -->
<!-- module:schedules -->
| Scheduled runs (pause, change, explain) | `_system/workflows/schedule.md` |
<!-- /module -->
| `/help` | `_system/HELP.md` |

Read only the workflow you need. When a workflow and this file disagree, this file wins —
then fix the workflow.

## Co-evolution

This schema is meant to change. When {{sage.owner.first_name}} corrects how something is filed, propose the
matching edit to this file or the relevant workflow, and log it as
`## [YYYY-MM-DD] schema | <what changed>`.
~~~~

`template/_system/tools/vault_config.py`:

~~~~python
#!/usr/bin/env python3
"""Read the vault's _system/config.json (written by sage-obsidian setup).

Import from other tools:  from vault_config import load, is_owner, owner_emails
Env override (tests): VAULT_ROOT
"""
import json
import os
from pathlib import Path


def root():
    return Path(os.environ.get("VAULT_ROOT") or Path(__file__).resolve().parents[2])


def load():
    p = root() / "_system/config.json"
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def owner_match():
    owner = load().get("owner", {})
    names = owner.get("match") or [owner.get("first_name", "")]
    return [str(n).lower() for n in names if str(n).strip()]


def is_owner(value):
    """True when a frontmatter value (assignee, author, link) names the vault owner."""
    text = str(value or "").lower()
    return any(m in text for m in owner_match())


def owner_emails():
    return {str(e).lower() for e in load().get("owner", {}).get("emails", [])}


def module_on(name):
    return bool(load().get("modules", {}).get(name))
~~~~

`template/_system/tests/test_vault_config.py`:

~~~~python
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
~~~~

`template/_system/tools/doctor.py`:

~~~~python
#!/usr/bin/env python3
"""File-level health checks for a sage-obsidian vault (read-only).

Usage: python3 _system/tools/doctor.py [--json]
Prints one line per check: "ok|warn|fail  <name>  <detail>  [→ fix]". Exit 1 if any check fails.
Connector reachability and scheduled tasks are checked by the doctor skill itself (they need Claude's
tools); this script covers everything visible on disk.
Env override (tests): VAULT_ROOT
"""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vault_config import load, root  # noqa: E402

SCHEMA_VERSION = 1


def run(*args):
    r = subprocess.run(list(args), cwd=root(), capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def checks():
    R = root()
    cfg = load()
    out = []
    add = lambda status, name, detail, fix="": out.append({"status": status, "name": name, "detail": detail, "fix": fix})
    if not cfg:
        add("fail", "config", "_system/config.json missing or invalid", "run sage-obsidian setup in this folder")
        return out
    v = cfg.get("schema_version")
    add("ok" if v == SCHEMA_VERSION else "fail", "config", f"schema v{v}, plugin {cfg.get('plugin_version', '?')}",
        "" if v == SCHEMA_VERSION else "run sage-obsidian upgrade")
    on = [k for k, val in cfg.get("modules", {}).items() if val]
    add("ok", "modules", ", ".join(["core"] + on))
    manifest = R / "_system/.framework-manifest.json"
    if manifest.is_file():
        missing = [p for p in json.loads(manifest.read_text()) if not (R / p).exists()]
        add("fail" if missing else "ok", "framework files",
            f"{len(missing)} missing: {', '.join(missing[:3])}" if missing else "all present",
            "run sage-obsidian setup (change mode) to restore them" if missing else "")
    else:
        add("warn", "framework files", "no .framework-manifest.json", "run sage-obsidian setup (change mode)")
    plugins = R / ".obsidian/community-plugins.json"
    enabled = json.loads(plugins.read_text()) if plugins.is_file() else []
    installed = {p.name for p in (R / ".obsidian/plugins").glob("*") if (p / "main.js").is_file()}
    for pid, label in [("dataview", "Dataview"), ("obsidian-tasks-plugin", "Tasks")]:
        if pid in installed and pid in enabled:
            add("ok", label, "installed and enabled")
        else:
            add("warn", label, "not installed" if pid not in installed else "installed but not enabled",
                f"Obsidian → Settings → Community plugins → install and enable {label}")
    dv = R / ".obsidian/plugins/dataview/data.json"
    dv_cfg = json.loads(dv.read_text()) if dv.is_file() else {}
    if cfg.get("modules", {}).get("dashboard"):
        add("ok" if dv_cfg.get("enableDataviewJs") else "fail", "Dataview JS queries",
            "on" if dv_cfg.get("enableDataviewJs") else "off",
            "" if dv_cfg.get("enableDataviewJs") else "Settings → Dataview → Enable JavaScript queries")
    code, text = run(sys.executable, "_system/tests/check_vault.py")
    add("ok" if code == 0 else "fail", "validator", text.splitlines()[-1] if text else "no output",
        "" if code == 0 else "run python3 _system/tests/check_vault.py and fix the FAIL lines")
    code, text = run("git", "status", "--porcelain")
    if code != 0:
        add("fail", "git", "not a git repository", "run: git init && git add -A && git commit -m 'setup'")
    else:
        n = len([l for l in text.splitlines() if l.strip()])
        add("ok" if n == 0 else "warn", "git", "clean" if n == 0 else f"{n} uncommitted changes",
            "" if n == 0 else "review with git status, then commit")
        code, remotes = run("git", "remote")
        add("ok" if not remotes else "fail", "git remote", "none (local only)" if not remotes else remotes,
            "" if not remotes else "remove it: git remote remove <name> (this vault must stay local)")
    lock = R / "_system/state/run.lock"
    if lock.is_file():
        try:
            started = datetime.fromisoformat(json.loads(lock.read_text())["started"].replace("Z", "+00:00"))
            hours = (datetime.now(timezone.utc) - started).total_seconds() / 3600
        except (ValueError, KeyError, json.JSONDecodeError):
            hours = 99
        add("warn" if hours > 2 else "ok", "run lock", f"held {hours:.1f}h",
            "python3 _system/tools/run_lock.py release" if hours > 2 else "")
    else:
        add("ok", "run lock", "free")
    pending = [p.name for p in (R / "_system/state/digests").glob("*.md") if "status: pending" in p.read_text()]
    add("warn" if pending else "ok", "digests", f"{len(pending)} pending" if pending else "none pending",
        "reply ok to the pending sync digest" if pending else "")
    return out


def main(argv):
    results = checks()
    if "--json" in argv:
        print(json.dumps(results, indent=2))
    else:
        for r in results:
            fix = f"  → {r['fix']}" if r["fix"] else ""
            print(f"{r['status']:<5} {r['name']:<20} {r['detail']}{fix}")
    return 1 if any(r["status"] == "fail" for r in results) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
~~~~

`template/_system/tests/test_doctor.py`:

~~~~python
#!/usr/bin/env python3
"""Tests for _system/tools/doctor.py. Run: python3 -m unittest _system/tests/test_doctor.py -v"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]


class DoctorTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "_system/tests").mkdir(parents=True)
        (self.root / "_system/state/digests").mkdir(parents=True)
        shutil.copytree(HERE / "tools", self.root / "_system/tools")
        (self.root / "_system/tests/check_vault.py").write_text("print('OK: stub (0 problems)')\n")

    def tearDown(self):
        self.tmp.cleanup()

    def doctor(self):
        env = dict(os.environ, VAULT_ROOT=str(self.root))
        r = subprocess.run([sys.executable, str(self.root / "_system/tools/doctor.py"), "--json"],
                           env=env, capture_output=True, text=True, cwd=self.root)
        return r.returncode, {c["name"]: c for c in json.loads(r.stdout)}

    def test_missing_config_fails(self):
        code, res = self.doctor()
        self.assertEqual(code, 1)
        self.assertEqual(res["config"]["status"], "fail")

    def test_healthy_vault(self):
        (self.root / "_system/config.json").write_text(json.dumps(
            {"schema_version": 1, "plugin_version": "0.1.0", "owner": {"first_name": "Jane"},
             "modules": {"dashboard": True}}))
        (self.root / ".obsidian/plugins/dataview").mkdir(parents=True)
        (self.root / ".obsidian/plugins/dataview/main.js").write_text("")
        (self.root / ".obsidian/plugins/dataview/data.json").write_text('{"enableDataviewJs": true}')
        (self.root / ".obsidian/community-plugins.json").write_text('["dataview"]')
        (self.root / "_system/.framework-manifest.json").write_text('{"_system/tools/doctor.py": "x"}')
        for args in (["init", "-q"], ["add", "-A"], ["-c", "user.name=t", "-c", "user.email=t@x", "commit", "-qm", "x"]):
            subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True)
        code, res = self.doctor()
        self.assertEqual(code, 0, res)
        self.assertEqual(res["Dataview"]["status"], "ok")
        self.assertEqual(res["Tasks"]["status"], "warn")
        self.assertEqual(res["git"]["status"], "ok")
        self.assertEqual(res["git remote"]["status"], "ok")
        self.assertEqual(res["validator"]["status"], "ok")

    def test_remote_and_old_schema_fail(self):
        (self.root / "_system/config.json").write_text(json.dumps({"schema_version": 0, "modules": {}}))
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "remote", "add", "origin", "https://example.com/x.git"], cwd=self.root, check=True)
        code, res = self.doctor()
        self.assertEqual(code, 1)
        self.assertEqual(res["config"]["status"], "fail")
        self.assertEqual(res["git remote"]["status"], "fail")

    def test_pending_digest_warns(self):
        (self.root / "_system/config.json").write_text(json.dumps({"schema_version": 1, "modules": {}}))
        (self.root / "_system/state/digests/d.md").write_text("---\ntype: digest\nstatus: pending\n---\n")
        _, res = self.doctor()
        self.assertEqual(res["digests"]["status"], "warn")


if __name__ == "__main__":
    unittest.main()
~~~~

`template/_system/tests/check_vault.py` (module-aware validator):

~~~~python
#!/usr/bin/env python3
"""Structural checks for a sage-obsidian vault (lists below are trimmed to the enabled modules at setup).

Usage: python3 _system/tests/check_vault.py [group ...]
Groups: skeleton schema pagetypes workflows commands obsidian sources tools (default: all)
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

WIKI_TYPES = {
    "person": "people", "project": "projects", "repo": "repos", "ticket": "tickets",
    "pr": "prs", "meeting": "meetings", "one-on-one": "one-on-ones",
    "concept": "concepts", "idea": "ideas", "decision": "decisions", "synthesis": "syntheses",
    "weekly": "weekly",
}
COMMON_FM = ["type", "title", "aliases", "status", "tags", "sources", "created", "updated"]
NO_STATUS = {"meeting", "concept", "synthesis", "weekly"}
EXTRA_FM = {
    "person": ["role", "team", "relation", "emails", "slack", "jira", "github"],
    "project": ["owner", "repos", "tickets", "start", "target"],
    "repo": ["url", "language", "owners"],
    "ticket": ["key", "url", "project", "assignee", "sprint"],
    "pr": ["repo", "number", "url", "author", "ticket"],
    "meeting": ["date", "attendees", "project"],
    "one-on-one": ["person", "cadence", "last"],
    "concept": [],
    "idea": ["origin", "effort", "impact"],
    "decision": ["date", "deciders", "supersedes"],
    "synthesis": ["question"],
    "weekly": ["week", "start", "end"],
}
RAW_DIRS = ["meetings", "one-on-ones", "slack", "claude-sessions", "thoughts", "clips", "assets", "email"]
SYSTEM_DIRS = ["workflows", "page-types", "templates", "tools", "tests", "state", "state/digests"]
INDEX_HEADINGS = ["People", "Projects", "Repos", "Tickets", "Pull requests", "Meetings",
                  "One-on-ones", "Concepts", "Ideas", "Decisions", "Syntheses", "Weekly"]
TODO_CATEGORIES = ["project", "follow-up", "review", "ticket", "idea", "growth"]
FULL_WORKFLOWS = [
    "ingest", "ingest-meeting", "ingest-1on1", "ingest-thought", "ingest-clip", "query", "lint", "inbox",
    "daily", "search",
    # module:sync
    "sync", "sync-status",
    # /module
    # module:todoist
    "todo-sync",
    # /module
    # module:schedules
    "schedule",
    # /module
    # module:weekly
    "weekly",
    # /module
    # module:prep
    "prep",
    # /module
    # module:dashboard
    "dash",
    # /module
]
STUB_WORKFLOWS = {}
ALL_SOURCES = ["drive-meetings", "jira", "slack", "gmail", "github-prs", "claude-sessions"]
POINTER_WORKFLOWS = {
    # module:source:drive_meetings
    "ingest-drive": "drive-meetings",
    # /module
    # module:source:jira
    "ingest-jira": "jira",
    # /module
    # module:source:slack
    "ingest-slack": "slack",
    # /module
    # module:source:gmail
    "ingest-email": "gmail",
    # /module
    # module:source:github_prs
    "ingest-pr": "github-prs",
    # /module
    # module:source:claude_sessions
    "ingest-claude-session": "claude-sessions",
    # /module
}
REQUIRED_SOURCES = list(POINTER_WORKFLOWS.values())
SOURCE_SECTIONS = ["## Fetch window", "## Fetch one item", "## Filter", "## Dedupe key",
                   "## Capture", "## Compile", "## Mode"]
DISCUSS_FIRST = ["ingest-meeting", "ingest-1on1", "ingest-thought"]
WRITING_WORKFLOWS = [
    "ingest", "inbox", "daily", "lint",
    # module:sync
    "sync",
    # /module
    # module:todoist
    "todo-sync",
    # /module
    # module:weekly
    "weekly",
    # /module
    # module:prep
    "prep",
    # /module
]
COMMANDS = {
    "ingest": "_system/workflows/ingest.md", "ask": "_system/workflows/query.md",
    "lint": "_system/workflows/lint.md", "inbox": "_system/workflows/inbox.md",
    "daily": "_system/workflows/daily.md", "help": "_system/HELP.md", "search": "_system/workflows/search.md",
    # module:sync
    "sync": "_system/workflows/sync.md", "sync-status": "_system/workflows/sync-status.md",
    # /module
    # module:todoist
    "todo-sync": "_system/workflows/todo-sync.md",
    # /module
    # module:weekly
    "weekly": "_system/workflows/weekly.md",
    # /module
    # module:prep
    "prep": "_system/workflows/prep.md",
    # /module
    # module:dashboard
    "dash": "_system/workflows/dash.md",
    # /module
}
TOOLS = [
    "_system/tools/run_lock.py", "_system/tools/search.py", "_system/tools/replace_block.py",
    "_system/tools/week_facts.py", "_system/tools/vault_config.py", "_system/tools/doctor.py",
    "_system/tests/test_run_lock.py", "_system/tests/test_search.py", "_system/tests/test_replace_block.py",
    "_system/tests/test_week_facts.py", "_system/tests/test_vault_config.py", "_system/tests/test_doctor.py",
    # module:todoist
    "_system/tools/todo_sync.py", "_system/tests/test_todo_sync.py",
    # /module
    # module:prep
    "_system/tools/prep_context.py", "_system/tests/test_prep_context.py",
    # /module
    # module:dashboard
    "_system/tools/dash_snapshot.py", "_system/tests/test_dash_snapshot.py",
    "_system/dashboard/command-center/view.js", "_system/dashboard/command-center/view.css",
    # /module
]

STUB_LINE = "Not implemented yet — see sub-project"

errors = []


def fail(msg):
    errors.append(msg)


def read(rel):
    p = ROOT / rel
    if not p.is_file():
        fail(f"missing file: {rel}")
        return ""
    return p.read_text(encoding="utf-8")


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    keys = {}
    for line in m.group(1).splitlines():
        km = re.match(r"^([A-Za-z][\w-]*):\s*(.*)$", line)
        if km:
            keys[km.group(1)] = km.group(2).strip()
    return keys


def need_dir(rel):
    p = ROOT / rel
    if not p.is_dir():
        fail(f"missing dir: {rel}")
    elif not any(p.iterdir()):
        fail(f"empty dir (needs .gitkeep for git): {rel}")


def check_skeleton():
    for d in RAW_DIRS:
        need_dir(f"raw/{d}")
    for folder in WIKI_TYPES.values():
        need_dir(f"wiki/{folder}")
    need_dir("journal")
    for d in SYSTEM_DIRS:
        need_dir(f"_system/{d}")
    index = read("index.md")
    for h in INDEX_HEADINGS:
        if f"\n## {h}\n" not in index:
            fail(f"index.md missing heading: ## {h}")
    log = read("log.md")
    if not re.search(r"^## \[\d{4}-\d{2}-\d{2}\] \w[\w-]* \| .+$", log, re.M):
        fail("log.md has no entry matching '## [YYYY-MM-DD] op | title'")
    if "## Inbox" not in read("inbox.md"):
        fail("inbox.md missing '## Inbox' heading")
    todos = read("todos.md")
    if "```tasks" not in todos:
        fail("todos.md has no ```tasks query block")
    for c in TODO_CATEGORIES:
        if f"#todo/{c}" not in todos:
            fail(f"todos.md missing category #todo/{c}")
    gi = read(".gitignore")
    for line in [".obsidian/workspace*.json", ".trash/", ".DS_Store", "__pycache__/"]:
        if line not in gi.splitlines():
            fail(f".gitignore missing line: {line}")


def check_schema():
    text = read("CLAUDE.md")
    if not text:
        return
    n = len(text.splitlines())
    if n > 130:
        fail(f"CLAUDE.md is {n} lines (max 130)")
    required = ["raw/", "wiki/", "_system/", "index.md", "log.md", "inbox.md", "todos.md",
                "journal/", "Never modify files in `raw/`", "sources:", "[!warning] Conflict",
                "git commit", "credentials", "aliases", "#todo/", "git remote",
                "normalize.md", "-raw", "sync_state.py", "sync-state.json", "config.json",
                # module:dashboard
                "home.md",
                # /module
                ]
    for phrase in required:
        if phrase not in text:
            fail(f"CLAUDE.md missing phrase: {phrase}")
    for wf in FULL_WORKFLOWS + list(STUB_WORKFLOWS) + list(POINTER_WORKFLOWS):
        if f"workflows/{wf}.md" not in text:
            fail(f"CLAUDE.md routing table missing workflows/{wf}.md")


def check_pagetypes():
    for t in WIKI_TYPES:
        spec = read(f"_system/page-types/{t}.md")
        fields = [f for f in COMMON_FM if not (f == "status" and t in NO_STATUS)] + EXTRA_FM[t]
        for f in fields:
            if f"`{f}`" not in spec:
                fail(f"page-types/{t}.md does not document field `{f}`")
        for h in ["## Frontmatter", "## Body sections", "## Rules"]:
            if h not in spec:
                fail(f"page-types/{t}.md missing heading {h}")
        tpl = read(f"_system/templates/{t}.md")
        fm = frontmatter(tpl)
        if fm is None:
            fail(f"templates/{t}.md has no frontmatter")
            continue
        if fm.get("type") != t:
            fail(f"templates/{t}.md type is {fm.get('type')!r}, expected {t!r}")
        for f in fields:
            if f not in fm:
                fail(f"templates/{t}.md frontmatter missing {f}")
        if t in NO_STATUS and "status" in fm:
            fail(f"templates/{t}.md must not have status")
        for h in ["## TL;DR", "## Related", "## Sources"]:
            if h not in tpl:
                fail(f"templates/{t}.md missing {h}")
    for p in sorted((ROOT / "wiki/people").glob("*.md")):
        fm = frontmatter(p.read_text(encoding="utf-8")) or {}
        for f in ["emails", "slack", "jira", "github"]:
            if f not in fm:
                fail(f"wiki/people/{p.name} frontmatter missing {f}")
    daily = read("_system/templates/daily.md")
    for h in ["## To-dos", "## Meetings", "## Ingested today", "## Meeting prep"]:
        if h not in daily:
            fail(f"templates/daily.md missing {h}")
    if not (ROOT / "_system/tools/gen_page_types.py").is_file():
        fail("missing _system/tools/gen_page_types.py")


def check_workflows():
    for wf in FULL_WORKFLOWS:
        text = read(f"_system/workflows/{wf}.md")
        if not text:
            continue
        if STUB_LINE in text:
            fail(f"workflows/{wf}.md should be full, but is a stub")
        if "## Steps" not in text:
            fail(f"workflows/{wf}.md missing '## Steps'")
    for wf in DISCUSS_FIRST:
        text = read(f"_system/workflows/{wf}.md")
        if "Discuss first" not in text or "wait for the user" not in text.lower():
            fail(f"workflows/{wf}.md must contain 'Discuss first' and 'wait for the user'")
        if "Finish" not in text:
            fail(f"workflows/{wf}.md must end by running 'Finish' from ingest.md")
    for wf in WRITING_WORKFLOWS:
        text = read(f"_system/workflows/{wf}.md")
        for phrase in ["log.md", "git commit"]:
            if phrase not in text:
                fail(f"workflows/{wf}.md missing '{phrase}'")
    ingest = read("_system/workflows/ingest.md")
    for phrase in ["## Finish", "index.md", "## Failure", "ingest-drive.md", "ingest-email.md"]:
        if phrase not in ingest:
            fail(f"workflows/ingest.md missing '{phrase}'")
    for wf, n in STUB_WORKFLOWS.items():
        text = read(f"_system/workflows/{wf}.md")
        if f"{STUB_LINE} {n}." not in text:
            fail(f"workflows/{wf}.md must contain '{STUB_LINE} {n}.'")
    for wf, src in POINTER_WORKFLOWS.items():
        text = read(f"_system/workflows/{wf}.md")
        if not text:
            continue
        if src in REQUIRED_SOURCES:
            if STUB_LINE in text or f"_system/sources/{src}.md" not in text or "## Steps" not in text:
                fail(f"workflows/{wf}.md must be a pointer to _system/sources/{src}.md with '## Steps'")
        elif f"{STUB_LINE} 2." not in text:
            fail(f"workflows/{wf}.md must stay a stub until {src} is built")
    lint = read("_system/workflows/lint.md")
    if "Stray root notes" not in lint:
        fail("workflows/lint.md missing 'Stray root notes' check")


def check_commands():
    help_text = read("_system/HELP.md")
    for cmd in COMMANDS:
        if f"/{cmd}" not in help_text:
            fail(f"HELP.md does not mention /{cmd}")
    for h in ["## Commands", "## Ingest modes", "## Where things live", "## Recipes", "## To-dos", "### Search",
              # module:sync
              "### Daily sync", "### First run",
              # /module
              # module:schedules
              "### Scheduled runs",
              # /module
              # module:prep
              "### Meeting prep",
              # /module
              # module:dashboard
              "### Command center",
              # /module
              ]:
        if h not in help_text:
            fail(f"HELP.md missing {h}")
    setup = read("_system/SETUP.md")
    for p in ["Dataview", "Tasks", "Templater", "Obsidian Git", "Web Clipper"]:
        if p not in setup:
            fail(f"SETUP.md does not mention {p}")


def load_json(rel):
    text = read(rel)
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        fail(f"{rel} is not valid JSON: {e}")
        return {}


def check_obsidian():
    app = load_json(".obsidian/app.json")
    expect = {"attachmentFolderPath": "raw/assets", "newLinkFormat": "shortest",
              "useMarkdownLinks": False, "newFileLocation": "root", "alwaysUpdateLinks": True}
    for k, v in expect.items():
        if app.get(k) != v:
            fail(f".obsidian/app.json {k} = {app.get(k)!r}, expected {v!r}")
    if load_json(".obsidian/templates.json").get("folder") != "_system/templates":
        fail(".obsidian/templates.json folder must be _system/templates")
    daily = load_json(".obsidian/daily-notes.json")
    for k, v in {"folder": "journal", "format": "YYYY-MM-DD",
                 "template": "_system/templates/daily"}.items():
        if daily.get(k) != v:
            fail(f".obsidian/daily-notes.json {k} = {daily.get(k)!r}, expected {v!r}")
    search = load_json(".obsidian/graph.json").get("search", "")
    for term in ["-path:_system", "-path:raw"]:
        if term not in search:
            fail(f".obsidian/graph.json search missing {term}")
    core = load_json(".obsidian/core-plugins.json")
    if core.get("sync") is not False:
        fail(".obsidian/core-plugins.json sync must be false (local-only vault)")
    for p in ["daily-notes", "templates", "backlink", "outgoing-link", "tag-pane", "graph"]:
        if core.get(p) is not True:
            fail(f".obsidian/core-plugins.json {p} must be true")


def check_sources():
    d = ROOT / "_system/sources"
    files = sorted(d.glob("*.md")) if d.is_dir() else []
    names = {f.stem for f in files}
    for s in REQUIRED_SOURCES:
        if s not in names:
            fail(f"missing source file: _system/sources/{s}.md")
    for f in files:
        if f.stem not in ALL_SOURCES:
            fail(f"unknown source file: _system/sources/{f.name}")
        t = f.read_text(encoding="utf-8")
        pos = -1
        for h in SOURCE_SECTIONS:
            i = t.find(f"\n{h}\n")
            if i == -1:
                fail(f"sources/{f.name} missing section {h}")
            elif i < pos:
                fail(f"sources/{f.name} section {h} out of order")
            pos = max(pos, i)
        if not re.search(r"\n## Mode\n+`(auto|digest)`", t):
            fail(f"sources/{f.name} '## Mode' must start with `auto` or `digest`")
    st = ROOT / "_system/state/sync-state.json"
    if st.exists():
        try:
            data = json.loads(st.read_text(encoding="utf-8"))
            if "sources" not in data:
                fail("sync-state.json has no 'sources' key")
        except json.JSONDecodeError as e:
            fail(f"sync-state.json is not valid JSON: {e}")
    dg = ROOT / "_system/state/digests"
    for p in sorted(dg.glob("*.md")) if dg.is_dir() else []:
        fm = frontmatter(p.read_text(encoding="utf-8")) or {}
        if fm.get("type") != "digest" or fm.get("status") not in ("pending", "applied"):
            fail(f"digest {p.name} needs frontmatter type: digest and status: pending|applied")
    for p in sorted((ROOT / "raw").rglob("*.md")):
        if "assets" in p.parts:
            continue
        if not re.search(r"-raw(-v\d+)?$", p.stem):
            fail(f"raw file missing -raw suffix: {p.relative_to(ROOT)}")
    for rel in [
        # module:sync
        "_system/tools/sync_state.py",
        # /module
        "_system/normalize.md",
    ]:
        if not (ROOT / rel).is_file():
            fail(f"missing file: {rel}")
    norm = (ROOT / "_system/normalize.md")
    if norm.is_file() and "| Heard as | Write as |" not in norm.read_text(encoding="utf-8"):
        fail("_system/normalize.md missing '| Heard as | Write as |' table")


def check_tools():
    for rel in TOOLS:
        read(rel)
    if "_system/state/run.lock" not in read(".gitignore"):
        fail(".gitignore must ignore _system/state/run.lock")
    if "## Cancelled" not in read("todos.md"):
        fail("todos.md missing '## Cancelled' view")
    claude = read("CLAUDE.md")
    for phrase in ["/search",
                   # module:todoist
                   "todo_sync.py",
                   # /module
                   # module:schedules
                   "schedule.md",
                   # /module
                   ]:
        if phrase not in claude:
            fail(f"CLAUDE.md missing '{phrase}'")
    for wf, phrases in {
        "query": ["search.py"], "daily": ["run_lock.py"],
        # module:todoist
        "todo-sync": ["todo_sync.py plan", "todo_sync.py apply", "run_lock.py"],
        # /module
        # module:sync
        "sync": ["Unattended mode", "run_lock.py"],
        # /module
        # module:weekly
        "weekly": ["week_facts.py", "run_lock.py", "impact-log", "--backfill"],
        # /module
        # module:prep
        "prep": ["prep_context.py", "list_events", "## Meeting prep", "run_lock.py"],
        # /module
        # module:dashboard
        "dash": ["dash_snapshot.py write", "list_events"],
        # /module
    }.items():
        text = read(f"_system/workflows/{wf}.md")
        for p in phrases:
            if p not in text:
                fail(f"workflows/{wf}.md missing '{p}'")
    # module:dashboard
    home = read("home.md")
    for p in ["cssclasses: [command-center]", 'dv.view("_system/dashboard/command-center")',
              "Enable JavaScript queries"]:
        if p not in home:
            fail(f"home.md missing '{p}'")
    view = read("_system/dashboard/command-center/view.js")
    for name in ["Header", "Tiles", "Today", "Inbox", "Board", "Hours", "Footer"]:
        if f'safe("{name}"' not in view:
            fail(f"command-center view.js missing section {name}")
    if "_system/state/dashboard.json" not in read(".gitignore"):
        fail(".gitignore must ignore _system/state/dashboard.json")
    # /module
    dv_cfg = load_json(".obsidian/plugins/dataview/data.json")
    for k in ["enableDataviewJs", "taskCompletionTracking", "taskCompletionUseEmojiShorthand"]:
        if dv_cfg.get(k) is not True:
            fail(f".obsidian/plugins/dataview/data.json must set {k}: true")
    cfg = load_json("_system/config.json")
    for key in ["schema_version", "owner", "modules"]:
        if key not in cfg:
            fail(f"_system/config.json missing '{key}'")
    if "home.md" not in read("_system/workflows/lint.md"):
        fail("workflows/lint.md must allow home.md at the vault root")


GROUPS = {"skeleton": check_skeleton, "schema": check_schema, "pagetypes": check_pagetypes,
          "workflows": check_workflows, "commands": check_commands, "obsidian": check_obsidian,
          "sources": check_sources, "tools": check_tools}


def main(argv):
    names = argv or list(GROUPS)
    for n in names:
        if n not in GROUPS:
            print(f"unknown group: {n}")
            return 2
        GROUPS[n]()
    for e in errors:
        print(f"FAIL: {e}")
    print(f"{'OK' if not errors else 'FAILED'}: {', '.join(names)} ({len(errors)} problems)")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
~~~~

Seeds — `template/index.md`:

~~~~markdown
---
type: index
title: Index
---
# Index

Catalog of every wiki page, by type. Claude keeps it current; newest first within a section.

## People

## Projects

## Repos

## Tickets

## Pull requests

## Meetings

## One-on-ones

## Concepts

## Ideas

## Decisions

## Syntheses

## Weekly
~~~~

`template/log.md`:

~~~~markdown
---
type: log
title: Log
---
# Log

Append-only. Newest at the bottom. Every entry starts with `## [YYYY-MM-DD] <op> | <title>`.
Last 5 entries: `grep "^## \[" log.md | tail -5`

## [{{sage.setup_date}}] setup | Vault created by sage-obsidian {{sage.plugin_version}}
- Owner: {{sage.owner.name}} · preset: {{sage.preset}}
~~~~

`template/inbox.md`:

~~~~markdown
---
type: inbox
title: Inbox
---
# Inbox

Quick capture. Write anything below as a bullet — a thought, a to-do, a link, a name.
Run `/inbox` and Claude will file each item and clear it from here.

## Inbox
~~~~

`template/_system/normalize.md`:

~~~~markdown
---
type: normalize
title: Name and term corrections
---
# Normalize

Transcripts and notes often mishear names and product terms. When Claude writes wiki pages it applies
these corrections (never to `raw/`). Add a row whenever you correct a name.

| Heard as | Write as |
|---|---|
~~~~

- [ ] **Step 4: Import** — `bash scripts/dev/import_vault.sh ~/Desktop/second-brain` → ends `template imported from …`. Then `echo '["dataview", "obsidian-tasks-plugin"]' > template/.obsidian/community-plugins.json`.
  Check: `grep -rln "<any banned string>" template` → nothing; `grep -rhoE "\{\{sage\.[A-Za-z0-9_.]+\}\}" template | sort -u` → only keys present in `presets/_base.json`.

- [ ] **Step 5: Verify rendered vaults** — for (engineer, all modules on + todoist) and (pm, every module off):
  `make_config.py` → `render_vault.py` → in the vault `git init && git add -A && git commit` → `python3 _system/tests/check_vault.py` → `OK … (0 problems)`; `python3 -m unittest discover -s _system/tests -p 'test_*.py'` → OK (80 tests all-on); `python3 _system/tools/doctor.py` → no `fail` lines.
  Then `python3 -m unittest discover -s scripts/tests` → OK.

- [ ] **Step 6: Commit** — `git add -A && git commit -m "feat: generic vault template, import tooling, leak test"` (check `git status` shows no `identity.local.json`).

---

### Task 4: Skills and packaging

**Files:** Create `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `scripts/tests/test_packaging.py`, `scripts/dev/gen_router_skills.py`, `skills/{setup,doctor,upgrade,help}/SKILL.md`, `skills/setup/reference/{connectors,schedules}.md`; generated `skills/<router>/SKILL.md` ×12.

- [ ] **Step 1: Failing test** — `scripts/tests/test_packaging.py`:

~~~~python
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
~~~~

`python3 -m unittest scripts/tests/test_packaging.py` → FAIL/ERROR (no manifests, no skills).

- [ ] **Step 2: Manifests** — `.claude-plugin/plugin.json`:

~~~~json
{
  "name": "sage-obsidian",
  "version": "0.1.0",
  "description": "Set up and run an Obsidian second brain kept by Claude: raw captures, a self-maintaining wiki, connector sync (Slack, Jira, Gmail, Drive meeting notes, GitHub PRs), Todoist, weekly synthesis, meeting prep and a command-center dashboard.",
  "author": {"name": "Balaji Challamalla"},
  "keywords": ["obsidian", "second-brain", "llm-wiki", "knowledge-base", "productivity"]
}
~~~~

`.claude-plugin/marketplace.json`:

~~~~json
{
  "name": "sage-obsidian",
  "owner": {"name": "Balaji Challamalla"},
  "plugins": [
    {
      "name": "sage-obsidian",
      "source": "./",
      "description": "Obsidian second brain kept by Claude — setup interview, connector sync, Todoist, weekly synthesis, meeting prep, dashboard."
    }
  ]
}
~~~~

- [ ] **Step 3: Router skills** — `scripts/dev/gen_router_skills.py`, then run it from the repo root:

~~~~python
#!/usr/bin/env python3
"""Generate the thin router skills (skills/<name>/SKILL.md). Run from the repo root after editing ROUTERS."""
import json
from pathlib import Path

ROUTERS = [
    ("ingest", "ingest", "File a source into the sage-obsidian vault: meeting notes, 1:1 notes, thoughts, clips, a Jira key, a Slack/Gmail/Drive/GitHub link. Use for \"file this\", \"add this to my vault\", \"ingest\".", "core"),
    ("ask", "query", "Answer a question from the sage-obsidian vault with [[citations]] and offer to save the answer. Use for \"ask my vault\", questions about my projects, people, meetings, decisions.", "core"),
    ("search", "search", "Ranked search over the sage-obsidian vault (titles, aliases, body; filters by type, date, person, tag). Use for \"find pages about…\", \"search my vault\".", "core"),
    ("lint", "lint", "Health-check the sage-obsidian vault's content (broken links, orphans, stale pages, conflicts, overdue to-dos) and fix approved issues. Use for \"lint my vault\", \"health check my notes\".", "core"),
    ("inbox", "inbox", "Triage inbox.md in the sage-obsidian vault: file every quick capture into the right page and clear it. Use for \"process my inbox\".", "core"),
    ("daily", "daily", "Create or refresh today's journal page in the sage-obsidian vault. Use for \"daily\", \"end of day\", \"refresh my journal\".", "core"),
    ("sync", "sync", "Pull new items from connectors (Slack, Jira, Gmail, Drive meeting notes, GitHub PRs, Claude sessions) into the sage-obsidian vault with one digest to review; supports --backfill. Use for \"sync my vault\".", "sync"),
    ("sync-status", "sync-status", "Show sage-obsidian sync status: cursors per source, backfill progress, pending digests. Use for \"sync status\".", "sync"),
    ("todo-sync", "todo-sync", "Two-way sync of the sage-obsidian vault's #todo/ checkboxes with Todoist. Use for \"sync my to-dos\", \"push to-dos to Todoist\".", "todoist"),
    ("weekly", "weekly", "Build this week's page in the sage-obsidian vault (shipped, decisions, progress, blockers, next week) and add wins to the impact log; supports --backfill. Use for \"weekly review\", \"what did I do this week\".", "weekly"),
    ("prep", "prep", "Meeting prep briefs from the sage-obsidian vault (last time, what I owe, what they owe, open questions); also the morning run for all of today's meetings. Use for \"prep me for <meeting or person>\".", "prep"),
    ("dash", "dash", "Refresh the sage-obsidian command-center dashboard data (calendar, Jira hours, Slack items needing me, PRs to review). Use for \"refresh my dashboard\", \"dash\".", "dashboard"),
]

BODY = """# {name}

1. **Find the vault.** The current working folder must contain `_system/config.json` (a sage-obsidian
   vault). If it doesn't, ask the user to open their vault folder (Cowork: choose it as the working
   folder; Claude Code: `cd` into it) or to run `sage-obsidian:setup` to create one. Never guess a path.
2. If the vault's `CLAUDE.md` is not already in context, read it.
3. If `_system/workflows/{wf}.md` does not exist, the **{module}** module is off in this vault: say so and
   that running `sage-obsidian:setup` again (change mode) turns it on. Stop.
4. Read `_system/workflows/{wf}.md` and follow it with the user's request and arguments.
5. Never add a git remote or push; never write secrets, compensation, health details or customer PII.
"""

for name, wf, desc, module in ROUTERS:
    d = Path("skills") / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text(f"---\nname: {name}\ndescription: {json.dumps(desc)}\n---\n" + BODY.format(name=name, wf=wf, module=module),
                                encoding="utf-8")
    print("wrote", d / "SKILL.md")
~~~~

- [ ] **Step 4: Main skills** — `skills/setup/SKILL.md`:

~~~~markdown
---
name: setup
description: "Create a new Obsidian second-brain vault kept by Claude (sage-obsidian): a short interview, connector checks, then the vault is built, git-initialised and health-checked. Also change mode: re-run inside an existing vault to add or remove modules and sources. Use for \"set up my second brain\", \"sage setup\", \"add Slack to my vault\"."
---
# sage-obsidian setup

You are setting up (or changing) a personal Obsidian vault that Claude maintains. Be brief and
friendly; use AskUserQuestion for every choice, with the recommended option first.

Plugin files: `${CLAUDE_PLUGIN_ROOT}` (scripts, presets, template). If that path is not visible to
the shell, find it: `find / -path '*sage-obsidian*/scripts/render_vault.py' 2>/dev/null | head -1`.
Call it `$P` below. Work in a scratch folder for `answers.json` / `config.json`.

## 0. Which mode?

- The working folder (or the folder the user names) contains `_system/config.json` → **change mode**
  (section 6).
- Otherwise → **new vault**. If the user has an existing Obsidian vault, do not touch it: create the
  new vault next to it; they can `/ingest` old notes later.

## 1. Interview (new vault)

Ask in four short rounds. Pre-fill what you can (name and email from the account/user context).

1. **You** — full name; work email; role preset (read `$P/presets/*.json` `label` + `description`:
   Engineer, Eng manager, PM, Data / analytics); timezone (default America/New_York).
2. **Vault** — folder (default `~/Desktop/second-brain`; if it exists and is not empty, propose
   `~/Desktop/second-brain-2`); vault name (default `second-brain`). In Cowork, request access to the
   parent folder with the directory tool first.
3. **Modules** (multi-select, preset defaults pre-selected) — Connector sync · Todoist sync · Scheduled
   runs · Weekly + impact log · Meeting prep · Dashboard. If sync is on: which sources (Slack, Jira,
   Gmail, Drive/Gemini meeting notes, GitHub PRs, Claude sessions).
4. **Details** (only for what's on) — Jira site (default xometry.atlassian.net) + project keys (e.g.
   MKTM); Slack channels worth watching; Drive meeting-notes folder; GitHub org (default xometry) +
   optional repo allowlist + PR review channels; Todoist project name (default Work); weekly hours
   target (default 40); schedule times (defaults 08:30 / 16:00 weekdays, Friday 15:00); how far back to
   backfill (default 8 weeks).

## 2. Connector check

For each needed connector, follow `reference/connectors.md`: probe with ToolSearch, then fetch the
user's IDs. Missing connector → tell the user exactly which one to add (Cowork: use the connector
suggestion tool if available; Claude Code: Settings → Connectors / `claude mcp`), then ask:
**Wait while I add it** (re-probe) · **Skip for now** (source stays off; enable later by re-running
setup) · **Turn this module off**.

## 3. Build

1. Write `answers.json` with only what you collected, e.g.
   `{"owner": {"name", "email", "timezone"}, "vault": {"name", "path"}, "modules": {...},
   "sources": {"slack": {"enabled", "user_id", "channels"}, "jira": {"enabled", "site", "cloud_id",
   "account_id", "projects"}, ...}, "todoist": {"project"}, "schedules": {...}, "dashboard": {"hours_target"},
   "sync": {"backfill_start": "YYYY-MM-DD"}}`.
2. `python3 $P/scripts/make_config.py --preset <preset> --answers answers.json --out config.json`
   (exit 2 names what's missing — ask for it).
3. Show a 6-line summary (owner, vault path, modules, sources, schedules) and ask **Create it?**
4. `python3 $P/scripts/render_vault.py --config config.json --out <vault path>`.
5. In the vault: `git init -q && git add -A && git commit -qm "setup: sage-obsidian v<version>"`.
   Never add a remote. (Cowork: if git leaves `*.lock` / `tmp_obj_*` files it can't delete, request
   delete permission for the folder, then `find .git \( -name 'tmp_obj_*' -o -name '*.lock' \) -delete`.)
6. Run the **doctor** skill steps (or `python3 _system/tools/doctor.py`).

## 4. Finish

Ask, one question each:
- **Scheduled runs** (if the module is on and the scheduled-tasks tool exists): create the tasks in
  `reference/schedules.md`, filling in the vault path and times. They run while the Claude app is
  open; a missed run happens at next launch — tell the user.
- **Obsidian**: open the folder as a vault (Obsidian → Open folder as vault), then install and enable
  **Dataview** and **Tasks** (Settings → Community plugins). The vault already ships Dataview's
  settings; toggle Dataview off/on once so it reads them.
- **First data** (if sync is on): start `/sync --backfill` now or later.

End with: the vault path, the 5 commands to try first (`/ingest`, `/ask`, `/sync`, `/daily`, `/dash`,
written as `/sage-obsidian:<name>` in Claude Code), and `/sage-obsidian:help`.

## 5. Rules

- One question at a time; never write outside the chosen vault folder and the scratch folder.
- Never store passwords, tokens or API keys. Connectors are the user's own Claude connectors.
- The vault is local-only git — never add a remote, never push.

## 6. Change mode (existing vault)

1. Read `_system/config.json`; show current modules and sources.
2. Ask what to add or remove (same choices as round 3–4); run the connector check for anything new.
3. Update the config: `python3 $P/scripts/make_config.py --preset <config.preset> --answers <changed
   fields merged into the old config> --out config.json`.
4. `python3 $P/scripts/render_vault.py --config config.json --out <vault> --update --dry-run`; show the
   files that will be written or removed; on **yes** run it without `--dry-run`. Notes in `raw/`,
   `wiki/`, `journal/` are never touched.
5. Commit `setup: modules <change>`; run doctor; create or delete scheduled tasks to match.
~~~~

`skills/setup/reference/connectors.md`:

~~~~markdown
# Connector check

Probe each connector with ToolSearch (the query below); "present" means at least one matching tool
loads. Then fetch the IDs listed. Connectors are the user's own — never ask for tokens or API keys.

| Needed for | Connector | ToolSearch query | IDs to fetch → config |
|---|---|---|---|
| source slack, dashboard Slack inbox | Slack | `slack search` | the user's Slack user ID (search users by their email or read their own profile) → `sources.slack.user_id` |
| source jira, dashboard hours | Atlassian (Jira) | `jira atlassian` | `getAccessibleAtlassianResources` → cloud ID for the site → `sources.jira.cloud_id`; `atlassianUserInfo` → `account_id` |
| source gmail, source github_prs (Cowork) | Gmail | `gmail search threads` | none |
| source drive_meetings | Google Drive | `google drive search files` | none (folder name only) |
| meeting prep, dashboard calendar | Google Calendar | `calendar list events` | none |
| todoist | Todoist | `todoist find tasks` | none (the Work project and sections are created on the first `/todo-sync`) |
| source claude_sessions | Session history (Cowork) | `list sessions transcript` | none |
| source github_prs (Claude Code) | `gh` CLI | run `gh auth status` | none |

If a probe finds nothing, name the connector and where to add it (Cowork: Settings → Connectors, or
the connector suggestion tool; Claude Code: `claude mcp add` / the connectors page), then offer:
wait and re-check · skip for now · turn the module off.
~~~~

`skills/setup/reference/schedules.md`:

~~~~markdown
# Scheduled runs (Cowork `create_scheduled_task`)

Create only the tasks whose modules are on. Replace `<VAULT>` with the vault path and use the cron
values from `config.schedules` (local time). Each prompt must be self-contained.

## vault-morning-sync — `config.schedules.morning` (default `30 8 * * 1-5`)

Second-brain vault — morning run (scheduled, unattended; nobody is there to reply).
Vault: <VAULT>. Read the vault's CLAUDE.md first.
1. If sync is on: follow _system/workflows/sync.md in **Unattended mode** (take the run lock, file and commit routine sources; Drive meeting notes and Gmail go into a pending digest — no wiki pages for them; never wait for a reply; release the lock).
2. If todoist is on: follow _system/workflows/todo-sync.md unattended (if the plan has needs_confirm true, drop cancel_local and delete_remote and report them).
3. If prep is on: follow the "Morning run" steps in _system/workflows/prep.md (one commit "prep: YYYY-MM-DD"; calendar unavailable → one-line skip note).
4. If dashboard is on: follow _system/workflows/dash.md last (no commit).
5. Golden rules: never edit raw/ after capture; no secrets, HR, health or compensation in the wiki; never add a git remote or push. If a run lock is held, stop and say so.
End with one summary line: filed automatically, waiting for an ok, to-dos synced, briefs written, dashboard sources ok/error.

## vault-end-of-day — `config.schedules.end_of_day` (default `0 16 * * 1-5`)

Second-brain vault — end-of-day run (scheduled, unattended).
Vault: <VAULT>. Read the vault's CLAUDE.md first.
1. Follow _system/workflows/daily.md (lock, refresh today's journal, log, commit, release; its last step runs todo-sync when that module is on).
2. If dashboard is on: follow _system/workflows/dash.md last (no commit).
3. Golden rules as above. End with one summary line.

## vault-weekly — `config.schedules.weekly` (default `0 15 * * 5`), only if weekly is on

Second-brain vault — weekly run (scheduled, unattended).
Vault: <VAULT>. Read the vault's CLAUDE.md first.
Follow _system/workflows/weekly.md for the current ISO week (lock, week_facts.py, write the weekly page from facts only, add (auto) wins to the impact log, index + log, one commit "weekly: <week>", release). Golden rules as above.
End with one line: the week's TL;DR and how many wins were added.
~~~~

`skills/doctor/SKILL.md`:

~~~~markdown
---
name: doctor
description: "Read-only health check of a sage-obsidian vault: config and schema version, module files, Obsidian plugins, connectors, scheduled runs, validator, git, run lock, pending digests — each with the fix. Use for \"doctor\", \"is my vault ok\", \"something's broken\"."
---
# sage-obsidian doctor (read-only — change nothing)

1. **Find the vault**: the working folder must contain `_system/config.json`; otherwise ask the user
   to open their vault folder or run `sage-obsidian:setup`.
2. Run `python3 _system/tools/doctor.py` (file checks: config, modules, plugins, Dataview JS,
   validator, git, git remote, run lock, digests).
3. **Connectors** — for each source enabled in `config.sources` (and Calendar if prep or dashboard is
   on, Todoist if todoist is on): probe with ToolSearch (queries in the setup skill's
   `reference/connectors.md`) and make one cheap read (e.g. a 1-result search). ok / fail + where to
   reconnect.
4. **Schedules** — if `modules.schedules` is on and the scheduled-tasks tool exists: list tasks and
   check `vault-morning-sync`, `vault-end-of-day` (and `vault-weekly` if weekly is on) exist and are
   enabled.
5. **Plugin version** — compare `config.plugin_version` with this plugin's `.claude-plugin/plugin.json`
   version; older → suggest `sage-obsidian:upgrade`.
6. Print one checklist, ✓ / ⚠ / ✗ per line with the fix, then one line: "All good" or "N things to fix".
~~~~

`skills/upgrade/SKILL.md`:

~~~~markdown
---
name: upgrade
description: "Bring a sage-obsidian vault's framework (workflows, tools, page types, dashboard, CLAUDE.md) up to the installed plugin version: per-file diffs, keeps the user's edits on request, runs migrations, never touches notes. Use for \"upgrade my vault\", after updating the plugin."
---
# sage-obsidian upgrade

`$P` = `${CLAUDE_PLUGIN_ROOT}` (if not visible to the shell:
`find / -path '*sage-obsidian*/scripts/render_vault.py' 2>/dev/null | head -1`, two levels up).

1. **Find the vault** (`_system/config.json` in the working folder). Take the run lock:
   `python3 _system/tools/run_lock.py acquire --owner upgrade` (exit 3 → stop and report).
2. Versions: `config.plugin_version` vs `$P/.claude-plugin/plugin.json`. Same → say "already up to
   date", release the lock, stop. Require a clean `git status` first (ask the user to commit or stash).
3. Copy `_system/config.json` to scratch, set `plugin_version` to the new version, then render the new
   framework into a scratch folder:
   `python3 $P/scripts/render_vault.py --config <scratch config> --out <scratch>/new`.
4. Compare: for each file in `<scratch>/new/_system/.framework-manifest.json`, the vault's
   `_system/.framework-manifest.json` hash tells whether the user edited it (current file hash ≠
   recorded hash).
   - Unchanged by the user → overwrite with the new file.
   - Edited by the user and the new version differs → show a short diff and ask: **take new** ·
     **keep mine** · **merge by hand** (write the new file next to it as `<name>.new` and say so).
   - New files → add. Files no longer in the new manifest → delete only if unedited; otherwise ask.
   Never touch `raw/`, `wiki/`, `journal/`, `inbox.md`, `index.md`, `log.md`, `_system/state/`.
5. Migrations: run every `$P/migrations/NNN_*.py` whose number is above `config.schema_version`, in
   order, with the vault as working directory; then set `schema_version` to the last one.
6. Write the new `_system/.framework-manifest.json` (from scratch/new) and the new `plugin_version`.
7. Run the doctor skill. Append `## [YYYY-MM-DD] upgrade | vX → vY` to `log.md` (list kept and merged
   files), commit `upgrade: vX → vY`, release the lock.
~~~~

`skills/help/SKILL.md`:

~~~~markdown
---
name: help
description: "Explain how to use a sage-obsidian vault and its commands; with a topic, show only that section. Before setup, explain what sage-obsidian is and how to start. Use for \"help\", \"how do I use my vault\", \"what commands are there\"."
---
# sage-obsidian help

1. If the working folder contains `_system/config.json`: read `_system/HELP.md`. With a topic, show
   only the matching section; otherwise show the Commands table and the Recipes headings. Commands in
   Claude Code are typed `/sage-obsidian:<name>`; in Cowork pick the skill or just ask.
2. Otherwise: explain in 5 lines what sage-obsidian does (raw captures → a wiki Claude maintains, with
   connector sync, Todoist, weekly synthesis, meeting prep and a dashboard) and that
   `sage-obsidian:setup` creates a vault in about five minutes. Point to the README for details.
~~~~

- [ ] **Step 5:** `python3 -m unittest discover -s scripts/tests` → `Ran 18 tests … OK`. If the `claude` CLI is available: `claude plugin validate .` → no errors.
- [ ] **Step 6: Commit** — `git add -A && git commit -m "feat: setup, doctor, upgrade, help and router skills; plugin manifests"`.

---

### Task 5: README, docs, packaging

**Files:** Create `README.md`, `docs/{connectors,customizing,troubleshooting}.md`, `CHANGELOG.md`, `LICENSE`, `migrations/README.md`, `scripts/package.sh`.

- [ ] **Step 1:** `README.md`:

~~~~markdown
# sage-obsidian

**A second brain that maintains itself.** Claude files your meetings, Slack threads, Jira tickets,
emails and PRs into an Obsidian wiki, keeps people/project/decision pages current, writes your weekly
impact summary, preps you for every meeting, and puts it all on one dashboard.

Built on Andrej Karpathy's *LLM Wiki* pattern: immutable **raw** captures → a **wiki** Claude
maintains → a **schema** (`CLAUDE.md`) that tells Claude how. Plain Markdown, local git, yours.

---

## What you get

| Command | What it does |
|---|---|
| `setup` | Interview → connector check → builds your vault (≈5 min). Re-run to add/remove modules. |
| `ingest` | File anything: meeting notes, 1:1s, thoughts, clips, a Jira key, a Slack/Gmail/Drive/GitHub link |
| `ask` · `search` | Answers with `[[citations]]` · ranked page search |
| `sync` · `sync-status` | Pull Slack, Jira, Gmail, Drive meeting notes, GitHub PRs, Claude sessions — one digest to review; `--backfill` for history |
| `daily` · `inbox` · `lint` | Journal page · triage quick captures · vault health |
| `todo-sync` | Two-way sync of `#todo/` checkboxes with Todoist |
| `weekly` | Week page (shipped, decisions, progress, blockers, next week) + running **impact log** |
| `prep` | Meeting brief: last time, what you owe, what they owe, open questions |
| `dash` | Refresh the **command center**: meetings, to-dos, Slack asks, PRs to review, ticket board, Jira hours |
| `doctor` · `upgrade` · `help` | Health check with fixes · bring your vault to the new version · guide |

In Claude Code commands are `/sage-obsidian:<command>`; in Cowork pick the skill or just ask
("sync my vault").

## Install

**Claude Code**
```
/plugin marketplace add <org>/sage-obsidian
/plugin install sage-obsidian@sage-obsidian
```

**Claude Cowork / claude.ai** — Customize → Plugins → **Add marketplace** → `<org>/sage-obsidian`,
then install *sage-obsidian*. (Or **Upload plugin** with `dist/sage-obsidian.zip` from
`scripts/package.sh`.)

## Set up in 5 minutes

1. Run **`sage-obsidian:setup`** and answer four short rounds: you · vault folder · modules · details.
2. Add any connectors it asks for (Settings → Connectors), or skip them for now.
3. Open the folder in Obsidian (**Open folder as vault**), then install and enable the **Dataview**
   and **Tasks** community plugins.
4. Run **`sage-obsidian:doctor`** — everything should be ✓.
5. Try `ingest` with today's meeting notes, then `ask` a question about them.

## Modules and connectors

| Module | Needs |
|---|---|
| Core (ingest, ask, search, lint, inbox, daily) | nothing |
| Connector sync | the connectors for the sources you pick: Slack · Atlassian (Jira) · Gmail · Google Drive · session history (Claude sessions); GitHub PRs via Gmail notifications (Cowork) or `gh` (Claude Code) |
| Todoist | Todoist connector |
| Scheduled runs | Cowork scheduled tasks (08:30 / 16:00 weekdays, Friday 15:00 — adjustable) |
| Weekly + impact log | nothing |
| Meeting prep · Dashboard | Google Calendar (dashboard also uses Slack, Jira, Gmail when on) |

Presets: **Engineer**, **Eng manager**, **PM**, **Data / analytics** — they only change the defaults.
Details: [docs/connectors.md](docs/connectors.md).

## Daily use

- Morning (automatic at 08:30): sync, to-dos, meeting briefs in your journal, dashboard refresh.
  Meetings and emails wait in a digest until you reply `ok`.
- During the day: `ingest` notes, `ask` questions, add to-dos from the dashboard.
- 16:00 (automatic): journal + to-do sync. Friday 15:00: weekly page + impact log.

## Customizing

Everything Claude follows lives in your vault as Markdown: `CLAUDE.md` (rules), `_system/workflows/`
(procedures), `_system/page-types/` (page shapes), `_system/sources/` (per-connector specs),
`_system/dashboard/` (the command center). Edit them freely — `upgrade` shows a diff and asks before
replacing anything you changed. See [docs/customizing.md](docs/customizing.md).

## Privacy and safety

- **Local only**: plain files + local git. Setup never adds a git remote; `doctor` flags one.
- **No credentials**: connectors are your own Claude connectors; nothing stores tokens or API keys.
- **Sensitive content stays out of the wiki**: compensation, health, HR, secrets and customer PII are
  kept only in `raw/` (or skipped) and logged as "sensitive content excluded".
- **Reviewable**: one commit per operation, an append-only `log.md`, and digests you approve before
  meeting notes or emails are filed.
- Don't turn on Obsidian Sync/iCloud for a vault with company-confidential notes.

## Upgrading

Update the plugin, open your vault, run **`sage-obsidian:upgrade`**. Your notes (`raw/`, `wiki/`,
`journal/`) are never touched.

## Troubleshooting

Run **`sage-obsidian:doctor`** first — every ✗ comes with its fix. More in
[docs/troubleshooting.md](docs/troubleshooting.md).

## FAQ

- **I already have a vault.** Setup creates a new one next to it; `ingest` old notes when useful.
- **Do I need every connector?** No — every module and source is optional.
- **Does it run when Claude is closed?** Scheduled runs need the Claude desktop app open; a missed run
  happens at next launch and the sync cursors catch up.

## Development

```
python3 -m unittest discover -s scripts/tests     # render, packaging, leak tests
scripts/package.sh                                 # builds dist/sage-obsidian.zip
```
Maintainers can re-import improvements from a working vault with `scripts/dev/import_vault.sh <vault>`
(needs a local, git-ignored `scripts/dev/identity.local.json`; see `identity.example.json`).

## Credits

[Andrej Karpathy — LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) ·
[kepano/obsidian-skills](https://github.com/kepano/obsidian-skills) for Obsidian syntax ·
built by Balaji Challamalla.
~~~~

- [ ] **Step 2:** `docs/connectors.md`:

~~~~markdown
# Connectors

sage-obsidian never stores credentials. It uses the connectors already on your Claude account.

| Source | Connector | What is pulled | Mode |
|---|---|---|---|
| Slack | Slack | Your messages, mentions and DMs; threads you're in | auto-filed |
| Jira | Atlassian | Tickets assigned to / reported by / watched by you in your project keys | auto-filed |
| Gmail | Gmail | Emails from people to you (newsletters, notifications, HR/payroll/health skipped) | digest — you approve |
| Drive meeting notes | Google Drive | Gemini "Notes by Gemini" docs | digest — you approve |
| GitHub PRs | Gmail notifications (Cowork) or `gh` (Claude Code) | PRs you authored or were asked to review | auto-filed |
| Claude sessions | Session history (Cowork) | Substantive work sessions | auto-filed |
| Calendar | Google Calendar | Today's events for meeting prep and the dashboard | read only |
| Todoist | Todoist | Two-way to-do sync in one project with a section per category | two-way |

Add a missing connector in Cowork under **Settings → Connectors**, then re-run `sage-obsidian:setup`
in your vault (change mode) to switch the source on.
~~~~

`docs/customizing.md`:

~~~~markdown
# Customizing your vault

- **Rules** — `CLAUDE.md`. Claude reads it before every command. Keep it under 130 lines.
- **Procedures** — `_system/workflows/<command>.md`. Change steps, add a recipe, or write a new
  workflow and a routing row in `CLAUDE.md`.
- **Page shapes** — edit the `TYPES` table in `_system/tools/gen_page_types.py` and run it; it rewrites
  `_system/page-types/` and `_system/templates/`.
- **A new source** — copy a file in `_system/sources/` and keep its sections (Fetch window, Fetch one
  item, Filter, Dedupe key, Capture, Compile, Mode).
- **Name fixes** — add rows to `_system/normalize.md` (e.g. "Core Logix" → "Coralogix").
- **Dashboard** — `_system/dashboard/command-center/view.js` and `view.css`.
- **Settings** — `_system/config.json`; re-run setup to apply module/source changes safely.

After editing, run `python3 _system/tests/check_vault.py`. `upgrade` keeps your edits: it shows a diff
and asks before replacing a file you changed.
~~~~

`docs/troubleshooting.md`:

~~~~markdown
# Troubleshooting

| Symptom | Fix |
|---|---|
| A command says "open your vault folder" | Cowork: choose the vault as the working folder. Claude Code: `cd` into it. |
| Dashboard shows code blocks | Install Dataview; Settings → Dataview → Enable JavaScript queries; toggle the plugin off/on. |
| Dashboard looks unstyled or doubled | Close and reopen `home.md`; run `doctor`. |
| `todos.md` shows code | Install and enable the Tasks plugin. |
| "run lock held" | Another run is in progress; if it is over 2 hours old: `python3 _system/tools/run_lock.py release`. |
| Sync source fails | Reconnect it under Settings → Connectors; `doctor` shows which one. |
| git "unable to unlink … Operation not permitted" (Cowork) | Allow file deletion for the vault folder when asked, then remove leftover `.git/*.lock` files. |
| Scheduled run didn't happen | The Claude app was closed; it runs at next launch. |
~~~~

`CHANGELOG.md`:

~~~~markdown
# Changelog

## 0.1.0 — 2026-10-20
First release for testers: setup interview with role presets and connector checks; core, connector
sync, Todoist, scheduled runs, weekly + impact log, meeting prep and command-center dashboard modules;
doctor, upgrade, help.
~~~~

`LICENSE` (confirm wording with Balaji before pushing):

~~~~
Copyright (c) 2026 Xometry, Inc. All rights reserved.
Internal use within Xometry only. Not for redistribution outside the company.
~~~~

`migrations/README.md`:

~~~~markdown
# Migrations

`NNN_<name>.py` scripts run in order by `upgrade` when a vault's `schema_version` is below NNN. Each
runs with the vault as the working directory, must be idempotent, and must not touch `raw/`. None yet:
schema version 1 is the first.
~~~~

- [ ] **Step 3:** `scripts/package.sh` (chmod +x):

~~~~bash
#!/usr/bin/env bash
# Build dist/sage-obsidian.zip for Cowork "Upload plugin". Runs the tests first.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m unittest discover -s scripts/tests >/dev/null
mkdir -p dist && rm -f dist/sage-obsidian.zip
zip -qr dist/sage-obsidian.zip .claude-plugin skills template presets scripts migrations docs README.md CHANGELOG.md LICENSE \
  -x 'scripts/dev/identity.local.json' -x '*/__pycache__/*' -x '*.DS_Store'
echo "dist/sage-obsidian.zip ($(du -h dist/sage-obsidian.zip | cut -f1))"
~~~~

Run it → `dist/sage-obsidian.zip (~176K)`; `unzip -l dist/sage-obsidian.zip | grep identity.local` → nothing.
- [ ] **Step 4: Commit** — `git add -A && git commit -m "docs: README, guides, changelog; package script"` (`dist/` is git-ignored).

---

### Task 6: Live acceptance (with Balaji)

- [ ] **Step 1: Install** — Cowork: Customize → Plugins → Upload plugin → `dist/sage-obsidian.zip` (or Claude Code: `/plugin marketplace add ~/Desktop/Sage-obsidian` → `/plugin install sage-obsidian@sage-obsidian`).
- [ ] **Step 2: Setup** — run `sage-obsidian:setup` into `~/Desktop/sage-test-vault` with the Engineer preset and every module on. Expected: connector check finds Slack, Atlassian, Gmail, Drive, Calendar, Todoist; IDs filled; vault built; one commit; doctor shows no ✗ (Dataview/Tasks ⚠ until installed).
- [ ] **Step 3: Use** — in the test vault: `sage-obsidian:ingest` a short note, `sage-obsidian:ask` about it, `sage-obsidian:sync slack` (one source), `sage-obsidian:dash`; open in Obsidian with Dataview + Tasks → dashboard renders.
- [ ] **Step 4: Change mode** — re-run setup in the test vault, turn Todoist off → `todo-sync` workflow and routing row removed, notes untouched, doctor clean.
- [ ] **Step 5: Hand-off** — fix anything found (each fix: test + commit); Balaji confirms the LICENSE text, creates the Xometry GitHub repo, adds the remote and pushes. Testers install with `/plugin marketplace add xometry/<repo>`.
