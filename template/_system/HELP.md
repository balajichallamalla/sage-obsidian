---
type: help
title: Vault help
---
# Second brain — how to use it

Commands come from the **sage-obsidian** plugin. In Claude Code type `/sage-obsidian:<command>`
(e.g. `/sage-obsidian:sync`); in Cowork pick the skill or just ask ("run sync").
This guide writes them short, as `/sync`.

## Commands

| Command | What it does | Example |
|---|---|---|
| `/ingest [path or text]` | Files a source into the wiki (auto-detects type) | `/ingest raw/meetings/2026-10-18-platform-sync.md` |
| `/ask <question>` | Answers from the wiki with `[[citations]]`; can save the answer | `/ask what did Jane and I agree about the rollout?` |
| `/lint` | Health check: broken links, orphans, stale pages, conflicts | `/lint` |
| `/inbox` | Files everything in `inbox.md` | `/inbox` |
| `/daily` | Builds/refreshes today's journal page | `/daily` |
<!-- module:sync -->
| `/sync [source…] [--backfill]` | Pulls new items from Drive meetings, Jira, Slack, Gmail, GitHub PRs, Claude sessions; one digest to review | `/sync` · `/sync jira slack` · `/sync --backfill` |
<!-- /module -->
<!-- module:sync -->
| `/sync-status` | Last sync per source, backfill progress, pending digest | `/sync-status` |
<!-- /module -->
<!-- module:todoist -->
| `/todo-sync` | Two-way sync of `#todo/` checkboxes with Todoist project **Work** | `/todo-sync` |
<!-- /module -->
| `/search <words> [filters]` | Ranked list of matching pages, no answer written | `/search nht --type decision` |
<!-- module:weekly -->
| `/weekly [YYYY-Www] [--backfill]` | Builds the week's page (shipped, decisions, progress, blockers, next week), adds wins to the impact log | `/weekly` · `/weekly 2026-W42` |
<!-- /module -->
<!-- module:prep -->
| `/prep <meeting or person>` | Brief for a meeting: last time, what you owe, what they owe, open questions | `/prep standup` · `/prep <name>` |
<!-- /module -->
<!-- module:dashboard -->
| `/dash` | Refreshes the dashboard's Slack, PR, Jira-hours and calendar data (no commit) | `/dash` |
<!-- /module -->
| `/help [topic]` | This guide, or one section of it | `/help recipes` |

## Ingest modes

| Source | Mode | What happens |
|---|---|---|
| Meeting notes | Discuss first | Claude shows takeaways, decisions, to-dos, pages to touch → you confirm → it writes |
| 1:1 notes | Discuss first | Same, plus a sensitive-content screen; updates the person's running 1:1 page |
| Thoughts / ideas | Discuss first | Claude splits items and proposes where each goes |
| Clips (articles) | Automatic | Concept / synthesis pages; review via `log.md` or `git diff` |
<!-- module:sync -->
| Drive meeting notes (Gemini) | Digest | Collected into the `/sync` digest; one OK files them |
<!-- /module -->
<!-- module:sync -->
| Gmail (emails from people) | Digest | Same; HR / payroll / health / legal threads are skipped |
<!-- /module -->
<!-- module:sync -->
| Jira, PRs, Slack, Claude sessions | Automatic | Filed during `/sync`; listed under "Filed automatically" |
<!-- /module -->

## Where things live

| Folder | Contents |
|---|---|
| `inbox.md` | Quick capture — dump anything here |
| `raw/` | Original captures, never edited |
| `wiki/people`, `projects`, `repos`, `tickets`, `prs` | Entity pages |
| `wiki/meetings`, `one-on-ones` | Meeting summaries; one running page per 1:1 person |
| `wiki/concepts`, `ideas`, `decisions`, `syntheses` | Knowledge, proposals, ADRs, saved answers |
| `journal/` | Daily pages |
| `todos.md` | Every open to-do, by category |
| `index.md` / `log.md` | Catalog of pages / history of changes |

## Recipes

### After a 1:1
1. Paste your notes: `/ingest` + the notes (mention the person's name).
2. Review Claude's summary and sensitive-exclusion list; correct anything.
3. Check `wiki/one-on-ones/1on1-<person>.md` → My commitments.

### After a meeting
1. `/ingest` + notes or transcript.
2. Confirm decisions and your to-dos.

### End of day
1. Dump loose thoughts into `inbox.md`.
2. `/inbox`, then `/daily`.

<!-- module:prep -->
### Prep for a 1:1 with someone
`/prep <name>` — uses the 1:1 page's open threads and commitments.

<!-- module:weekly -->
<!-- /module -->
### Weekly
Friday 15:00 the weekly page is built automatically. Read it, edit or delete `(auto)` wins in
[[impact-log]], then `/lint` and fix the top suggestions.

<!-- module:sync -->
<!-- /module -->
### Daily sync
1. `/sync`
2. Review the digest → reply `ok`, `ok, but …`, or `skip <item>`.
3. `/daily`

<!-- /module -->
<!-- module:sync -->
### First run
Run `/sync --backfill` repeatedly — one week per run from {{sage.sync.backfill_start}} — until
`/sync-status` shows backfill done for every source.

<!-- /module -->
<!-- module:schedules -->
### Scheduled runs
- 08:30 Mon–Fri: connector sync (routine sources filed; meetings/emails wait in a digest) + to-do sync + meeting prep briefs in today's journal.
- Fri 15:00: weekly page + impact log + home "This week".
- 16:00 Mon–Fri: today's journal page + to-do sync.
- App closed at the time? The run happens at next launch and catches up. Manage them under **Scheduled** in the Cowork sidebar, or ask "pause vault-morning-sync".

<!-- /module -->
### Search
`/search <words>` for a ranked list; filters `--type`, `--since`, `--until`, `--person`, `--tag`, `--raw`.
`/ask` uses the same search before answering.

<!-- module:prep -->
### Meeting prep
Every weekday at 08:30 each of today's meetings gets a 3–6 line brief under `## Meeting prep`
in the journal (large meetings and focus blocks are skipped). On demand: `/prep <meeting or person>`.

<!-- /module -->
<!-- module:dashboard -->
### Command center
Open `home.md` (pin it as a tab). Tickets, to-dos, meetings briefs, journal and this week are live
from the vault. Slack items, PRs to review, Jira hours and today's calendar come from a snapshot
refreshed at 08:30, 16:00 and whenever you run `/dash`; each section says when it's stale.
Add a to-do with the box on the dashboard — it lands in today's journal and reaches Todoist on the
next sync. Needs Dataview with **Enable JavaScript queries** and Tasks (see SETUP).

<!-- /module -->
## To-dos

Write `- [ ] text #todo/<category> 📅 YYYY-MM-DD` anywhere. Categories:
`project`, `follow-up`, `review`, `ticket`, `idea`, `growth`.
See them all in `todos.md`. They mirror to Todoist project **Work** (a section per category):
tick in either place; deleting in Todoist marks the line `- [-]` (cancelled); deleting the
line in the vault deletes the Todoist task. Due-date changes in Todoist stay in Todoist.
