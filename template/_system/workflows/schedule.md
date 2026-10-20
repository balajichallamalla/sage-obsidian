---
type: workflow
title: Scheduled runs
---
# Workflow: schedule

Cowork scheduled tasks run the vault ({{sage.owner.timezone}}; Cowork adds a few
minutes of dispatch delay). They run while the Claude desktop app is open; a run that was due
while the app was closed runs at the next launch. Either way the sync cursors make it catch up.
Both tasks are saved in Auto mode (tools run without asking; they pause if something looks
unsafe) — switch to "Manually approve" in the task's settings if preferred.

| Task | When | What it does |
|---|---|---|
| `vault-morning-sync` | 08:30 Mon–Fri | `vault-sync` in unattended mode, then `vault-todo-sync` |
| `vault-end-of-day` | 16:00 Mon–Fri | `vault-daily`, then `vault-todo-sync` |

## Steps

1. Scheduled runs follow `sync.md` **Unattended mode**: routine sources file and commit; Drive
   meetings and Gmail go into a pending digest and nothing from them reaches the wiki until
   {{sage.owner.first_name}} replies `ok`.
2. Every run takes the lock first (`python3 _system/tools/run_lock.py acquire --owner <name>`);
   if a manual run holds it, the scheduled run stops and says so.
3. To pause, change times, or delete: use the scheduled-tasks controls in Cowork (or ask
   "pause vault-morning-sync"). Log changes as `## [YYYY-MM-DD] schema | schedule: <change>`.
