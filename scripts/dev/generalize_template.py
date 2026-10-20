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
