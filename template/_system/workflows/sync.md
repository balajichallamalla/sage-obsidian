---
type: workflow
title: Sync
---
# Workflow: sync (/sync)

Sweep connectors for new items since the last run, file routine items automatically, and
collect meetings/emails into one digest for {{sage.owner.first_name}}'s OK. Spec:
`_system/specs/2026-10-18-connector-ingestion-design.md`.

**Usage:** `/sync` (all built sources) · `/sync jira slack` (named sources) · `/sync --backfill`
(next 7-day historical window per source).

**Unattended mode** (scheduled runs; no one is there to reply): never wait for a reply.
Step 1 — if a digest is already pending, skip digest-mode sources this run. Step 4 — write the
digest with `status: pending` and add `pending_windows: {<source>: <END>}` to its frontmatter;
do not capture or compile digest-mode items and do not advance their cursors. Step 5 — skip.
Step 6 — mark/advance only auto-mode sources. Report "Digest waiting: N meetings, M emails —
reply `ok` to file." When {{sage.owner.first_name}} later replies `ok` to a pending digest that has
`pending_windows`, capture and compile its items, then advance each listed source to its END.

## Steps

0. **Lock.** `python3 _system/tools/run_lock.py acquire --owner sync` — exit 3 → stop and report.
1. **Pending digest check.** If any `_system/state/digests/*.md` has `status: pending`, ask
   {{sage.owner.first_name}}: apply it first, or merge new items into it. Wait for the answer.
2. **Pick sources.** Requested sources (default: all) in this order: `drive-meetings`, `jira`,
   `slack`, `gmail`, `github-prs`, `claude-sessions`. A source with no file in
   `_system/sources/` is reported as "not built yet" and skipped.
3. **Per source** (read `_system/sources/<source>.md` first):
   1. `python3 _system/tools/sync_state.py window <source> [--backfill]` → `START END`
      (or `DONE` → backfill finished for that source; skip it).
   2. Follow `## Fetch window` for `[START, END)`. If results exceed the page limit stated
      there, `python3 _system/tools/sync_state.py split START END` and process each half.
   3. Apply `## Filter`. For each remaining item:
      `python3 _system/tools/sync_state.py seen <source> <id> --version <v>` →
      exit 0 skip · exit 1 new · exit 2 changed (update path in `## Compile`).
   4. `## Capture` (raw file ending `-raw.md`; re-capture `-raw-v2.md`), when the source has one.
   5. Mode `auto`: run `## Compile` now, applying `_system/normalize.md`.
      Mode `digest`: add an entry to the digest (step 4) — do not write wiki pages yet.
   6. On connector/auth error: `python3 _system/tools/sync_state.py run <source> --status error
      --fetched 0 --new 0 --updated 0 --note "<error>"`, leave its cursor alone, note it for the
      digest's Conflicts section, continue with the next source.
   7. Keep a list of `(source, id, path, version)` for every filed or skipped item.
4. **Digest.** Write `_system/state/digests/YYYY-MM-DD-HHmm.md`:
   ```
   ---
   type: digest
   status: pending
   window: <earliest START> → <latest END>
   sources: [<sources run>]
   ---
   # Sync digest — YYYY-MM-DD HH:mm

   ## Filed automatically
   - <source>: N new, M updated — [[page]], [[page]] …

   ## Needs your OK
   ### Meeting: <title> (<date>)
   - Takeaways: …
   - Decisions: … (★ = gets its own decision page)
   - Your to-dos: - [ ] … #todo/<cat> 📅 YYYY-MM-DD
   - Others: …
   - Pages to touch: …
   ### Email: "<subject>" from <sender>
   - (same shape, shorter)

   ## Conflicts / questions
   - unmatched people, contradictions, re-captures, connector errors

   Reply: `ok` · `ok, but …` · `skip <item>`
   ```
   Show it to {{sage.owner.first_name}}, then wait for the user's reply. If nothing needs an OK, say so and go to step 6.
5. **Apply.** `ok` → compile every "Needs your OK" item via its source's `## Compile`.
   `ok, but …` → apply corrections first. `skip <item>` → leave its raw file, record it with
   path `skipped`. Update the digest to `status: applied`.
6. **Finish (one commit).**
   1. Bump `updated:` on touched pages; add/refresh `index.md` lines for new pages.
   2. For every filed/skipped item: `python3 _system/tools/sync_state.py mark <source> <id> <path> --version <v>`.
   3. For every source that succeeded: `python3 _system/tools/sync_state.py advance <source> <END> [--backfill]`
      and `python3 _system/tools/sync_state.py run <source> --status ok --fetched N --new N --updated N`.
   4. Append to `log.md`:
      `## [YYYY-MM-DD] sync | <N> new, <M> updated (<source>: n, …)` with bullets for pages
      created/updated, to-dos added, skipped items, sensitive items skipped (count only), errors.
   5. `git add -A && git commit -m "sync: YYYY-MM-DD — <N> new, <M> updated"`, then
      `find .git \( -name 'tmp_obj_*' -o -name '*.lock' \) -delete`, then `python3 _system/tools/run_lock.py release`.
   6. If the commit fails: `git checkout -- _system/state/sync-state.json` so cursors never
      run ahead of committed content; report the error.
7. **Report** in chat: per-source counts, digest link, to-dos added, anything needing attention.

<!-- module:todoist -->
8. **To-dos.** Run `_system/workflows/todo-sync.md` (own lock, own commit).
<!-- /module -->

## Failure

Anything fails before step 6.5: no commit, no cursor movement. List touched files
(`git status --short`); {{sage.owner.first_name}} reviews with `git diff`. The next `/sync` re-fetches the same
windows and `seen` prevents duplicates.
Always run `python3 _system/tools/run_lock.py release` before stopping.
