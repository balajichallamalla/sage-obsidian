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
