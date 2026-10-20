---
type: workflow
title: Todo sync
---
# Workflow: todo-sync (/todo-sync)

**Mode: automatic.** Mirrors `#todo/` checkboxes into Todoist project **Work** (one section per
category). Spec: `_system/specs/2026-10-19-todoist-scheduling-search-design.md`.

- Vault → Todoist: new open checkboxes are created; vault ticks complete; vault edits update
  (only when the line changed since the last sync); removed lines and `- [-]` delete.
- Todoist → vault: completions tick (`✅`); deletions cancel (`- [-] … ❌`).
- Todoist due-date changes and Todoist-only tasks are not pulled.

## Steps

1. **Lock.** `python3 _system/tools/run_lock.py acquire --owner todo-sync`. Exit 3 → stop and
   report who holds it.
2. **Project and sections.** Find project **Work** (`find-projects`); create it if missing
   (`add-projects`). Find its sections (`find-sections`); create any missing of `Follow-ups`,
   `Reviews`, `Tickets`, `Project work`, `Ideas`, `Growth` (`add-sections`). Write
   `{"follow-up": id, "review": id, "ticket": id, "project": id, "idea": id, "growth": id}` to
   `/tmp/todoist-sections.json` and run
   `python3 _system/tools/todo_sync.py record-project <project_id> /tmp/todoist-sections.json`.
3. **Remote state.** `find-tasks` with the Work project id — follow every page — and collect all
   open task ids. `find-completed-tasks` for the Work project since the state cursor
   (`python3 _system/tools/todo_sync.py status` shows it; first run: last 30 days). Write
   `/tmp/todoist-remote.json` = `{"open": [ids], "completed": [{"id", "completed_at"}]}`.
4. **Plan.** `python3 _system/tools/todo_sync.py plan --remote /tmp/todoist-remote.json >
   /tmp/todoist-plan.json`. Show warnings. If `needs_confirm` is true: in an attended run show
   the `cancel_local` / `delete_remote` lists and wait for the user's OK; in an unattended run
   drop those two lists from the plan and report them.
5. **Execute** (batch where the tool allows, ≤ 25 per call):
   - `create` → `add-tasks` with `content`, `description`, `projectId`, `sectionId` =
     sections[`section`], `dueString` = `due` (omit if null). Put the returned id on each entry.
   - `complete_remote` → `complete-tasks` by id.
   - `update_remote` → `update-tasks` with `content` (and move to the section if it changed);
     dates via `reschedule-tasks` (`due` null → remove the date).
   - `delete_remote` → `delete-object` (type task) by id.
   - `tick_local`, `cancel_local` → no Todoist call; pass through.
   Write `/tmp/todoist-results.json`: the plan with only the entries that succeeded, plus
   `"errors": ["<what failed>"]` for failures.
6. **Apply.** `python3 _system/tools/todo_sync.py apply /tmp/todoist-results.json`. List any
   `skipped` lines (edited during the run) — the next run retries them.
7. **Finish.** Append to `log.md`:
   `## [YYYY-MM-DD] todo-sync | +N created, N done, N cancelled, N updated, N deleted`
   (bullets for warnings, skipped lines, errors). Then
   `git add -A && git commit -m "todo-sync: YYYY-MM-DD HH:MM"`,
   `find .git \( -name 'tmp_obj_*' -o -name '*.lock' \) -delete`,
   `python3 _system/tools/run_lock.py release`.
8. **Report** the counts in one line. Nothing changed → no log entry, no commit; still release
   the lock.

## Failure

A Todoist call fails → apply what succeeded (step 6) and list the rest under errors; unsent
creates have no `🆔` yet, so the next run retries them. Any other failure before step 7: no
commit — `git checkout -- _system/state/sync-state.json` and the touched pages, release the
lock, report.
