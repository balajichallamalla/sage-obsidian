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
