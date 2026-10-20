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
