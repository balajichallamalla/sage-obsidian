---
type: workflow
title: Meeting prep
---
# Workflow: prep (/prep <meeting or person> · morning run)

**Mode: automatic** in the morning run; **read-only** on demand unless {{sage.owner.first_name}} says "save".
Briefs come only from the vault (`prep_context.py`) and the calendar event. Never show content
excluded as sensitive; it is not in the wiki and must not be pulled from `raw/`.

## Steps

### Morning run (inside the 08:30 scheduled run, after sync and todo-sync)

1. `python3 _system/tools/run_lock.py acquire --owner prep` — exit 3 → stop and report.
2. Google Calendar `list_events` for today (primary calendar, ordered by start time).
   Failure → write `Meeting prep skipped: calendar unavailable` under `## Meeting prep` in
   today's journal and go to step 6.
3. Skip: events {{sage.owner.first_name}} declined, all-day events, focus/OOO/"block" events, and events with no
   other attendees. Events with more than 15 attendees get one line only:
   `- HH:MM **<title>** — large meeting, no brief`.
4. For each remaining event run
   `python3 _system/tools/prep_context.py --title "<title>" --emails "<Name <email>>,…" --date <today> --json`
   and write a 3–6 line brief:
   ```markdown
   ### HH:MM <title>
   - Last time: [[<recurring.path stem>]] — <one-line gist>; open action items: …
   - I owe: <open_todos and my_commitments_open, with [[links]]>
   - They owe: <their_commitments, action items owned by them>
   - Open questions: <open_threads, blocked tickets>
   - Links: <related, tickets_in_progress>
   ```
   Drop lines that would be empty. A 1:1 uses the 1:1 page's open threads and commitments.
5. Open `journal/<today>.md` (create from `_system/templates/daily.md` if missing) and replace
   the `## Meeting prep` section with the briefs, in start-time order.
6. Append `## [YYYY-MM-DD] prep | N briefs` to `log.md`,
   `git add -A && git commit -m "prep: YYYY-MM-DD"`, then
   `find .git \( -name 'tmp_obj_*' -o -name '*.lock' \) -delete` and
   `python3 _system/tools/run_lock.py release`.

### On demand (`/prep <meeting title or person>`)

1. Meeting title → Google Calendar `list_events` (or `search_events`) for today through the next
   7 days; person → the next event with that person's email (from their person page `emails`).
2. Steps 3–4 above for that one event; show the brief in chat.
3. Offer: "Save it to the journal?" On yes: steps 5 and 6 (lock first, one commit).

### After the meeting

When the meeting's notes are filed (`ingest-meeting.md`), the meeting page links the journal
day in `## Related` (`[[journal/YYYY-MM-DD#Meeting prep]]`).
