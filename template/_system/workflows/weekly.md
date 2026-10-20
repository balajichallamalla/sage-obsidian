---
type: workflow
title: Weekly
---
# Workflow: weekly (/weekly [YYYY-Www] [--backfill])

**Mode: automatic.** Builds one weekly page from exact facts, adds wins to the impact log (the
home dashboard reads both directly). Safe to re-run: it rewrites the week's page and never duplicates wins.
Scheduled run: Friday 15:00 (`vault-weekly`, see `schedule.md`).

## Steps

1. `python3 _system/tools/run_lock.py acquire --owner weekly` — exit 3 → stop and report.
2. Week = the argument, else the current ISO week. Run
   `python3 _system/tools/week_facts.py --week <week> --json` and use **only** its output plus
   the pages it points to. Never invent items.
3. **Write `wiki/weekly/<week>.md`** from `_system/templates/weekly.md`
   (page type `_system/page-types/weekly.md`). Keep `created` if the page exists.
   - Frontmatter: `title: "Week NN (Mon D – Mon D, YYYY)"`, `aliases: [<week>]`, `tags: [weekly]`,
     `week`, `start`, `end` from the facts; `sources:` = `[[links]]` to every page cited below.
   - `## TL;DR` — up to 3 lines: the biggest shipped item, the main decision, the main blocker.
   - `## Shipped` — `prs_merged`, `tickets_closed`, and `projects_active` tagged `automation`;
     one bullet each: `- [[link]] — what shipped (date)`.
   - `## Decisions` — `decisions`: `- [[link]] — title`.
   - `## Progress by project` — one line per `projects_active` entry, summarising its `bullets`.
   - `## Open loops & blockers` — `blocked`, `todos_overdue`, `digests_pending`.
   - `## Next week` — `todos_next_week` and `my_tickets_open`.
   - `## Numbers` — meetings `len(meetings)`, pages created/updated, to-dos done/added, log entries.
   - `## Related` — `[[impact-log]]`, previous and next week pages if they exist.
   - `## Sources` — the cited pages and `log.md`.
   - Quiet week (no meetings, decisions, shipped items, project activity or done to-dos):
     TL;DR `Quiet week — nothing was filed in the vault.`; other sections `- none`.
4. **Impact log** `wiki/syntheses/impact-log.md` (create it from the shape below if missing).
   For each `wins` entry whose `link` is not already on the page, add under its month heading
   `## YYYY-MM` (newest month first; create the heading if missing):
   `- YYYY-MM-DD — <what> — <impact, numbers only if a cited page states them> — [[link]] (auto)`.
   Read the linked page's TL;DR for "what" and "impact". Then refresh `## TL;DR`
   (`N wins logged.` + top 3 by impact), add the link to `sources:`, bump `updated:`.
   {{sage.owner.first_name}} edits or deletes `(auto)` lines. To respect deletions, also skip any link already
   listed as added under an earlier `weekly |` entry in `log.md`.
5. **Finish:** `index.md` → under `## Weekly`, add or refresh `- [[<week>]] — <first TL;DR line>`
   (newest first). Append to `log.md`:
   `## [YYYY-MM-DD] weekly | <week>` with bullets for wins added and counts.
   `git add -A && git commit -m "weekly: <week>"`, then
   `find .git \( -name 'tmp_obj_*' -o -name '*.lock' \) -delete` and
   `python3 _system/tools/run_lock.py release`.

## Backfill (`/weekly --backfill`)

Run steps 2–4 for every week from the ISO week of `{{sage.sync.backfill_start}}` to the current week, oldest
first, then step 5 once with the log title
`backfill 2026-W35..<week>` and commit `weekly: backfill 2026-W35..<week>`.
Ask {{sage.owner.first_name}} for 3–6 past wins worth seeding (find each page with `search.py`; skip any already present) and add them as `(auto)` lines.

## Impact log shape

```markdown
---
type: synthesis
title: Impact log
aliases: [impact log, wins, brag doc]
tags: [impact]
sources: []
created: YYYY-MM-DD
updated: YYYY-MM-DD
question: "What have I delivered?"
---
# Impact log

## TL;DR
0 wins logged.

## Related
[[home]] · weekly pages under `wiki/weekly/`

## Sources
```

Month sections (`## 2026-10`, `## 2026-09`, …) go between `## TL;DR` and `## Related`.

## Failure

- `week_facts.py` error → stop, release the lock, report the error. Nothing is committed.
- A cited page is missing → leave the item out and note it in the log entry.
