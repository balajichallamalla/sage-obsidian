---
type: workflow
title: Daily
---
# Workflow: daily (/daily)

**Mode: automatic.** Safe to run several times a day — it refreshes, never duplicates.

## Steps

1. `python3 _system/tools/run_lock.py acquire --owner daily` — exit 3 → stop and report.
2. Open `journal/YYYY-MM-DD.md` for today; if missing, create it from
   `_system/templates/daily.md` (replace `{{date:YYYY-MM-DD}}` with today).
3. `## Ingested today`: replace the section with one bullet per `log.md` entry dated today:
   `- <op> — <title>` linking the main page.
4. `## Meetings`: replace with links to `wiki/meetings/<today>-*.md` and 1:1 pages whose
   `last:` is today.
5. `## To-dos`: keep everything already there. Append (no duplicates) any new checkboxes
   created today on other pages as `- [[page]]: <task text>` pointers.
6. Leave `## Focus` and `## Notes` untouched — those are {{sage.owner.first_name}}'s. Leave `## Meeting prep` to `prep.md`.
7. Append `## [YYYY-MM-DD] daily | refreshed journal` to `log.md` (once per day; if an entry
   for today exists, skip) and `git add -A && git commit -m "daily: YYYY-MM-DD"`, then
   `find .git \( -name 'tmp_obj_*' -o -name '*.lock' \) -delete` and
   `python3 _system/tools/run_lock.py release`.
<!-- module:todoist -->
8. Run `_system/workflows/todo-sync.md` (it takes its own lock and makes its own commit).
<!-- /module -->
