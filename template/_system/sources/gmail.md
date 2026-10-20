---
type: source
title: Source — Gmail
---
# Source: gmail

Connector: Gmail (`search_threads`, `get_thread`).

## Fetch window
- Convert START/END to Unix seconds.
- `search_threads` with query:
  `to:me after:<START_UNIX> before:<END_UNIX> -from:(notifications@github.com OR jira@{{sage.sources.jira.site}} OR gemini-notes@google.com OR no-reply@todoist.com OR calendar-notification@google.com) -from:noreply -from:no-reply -category:promotions -category:social -category:updates -category:forums {{sage.sources.gmail.exclude}} -subject:(Invitation OR "Updated invitation" OR Accepted OR Declined)`,
  `pageSize: 50`, `view: THREAD_VIEW_MINIMAL`; follow `nextPageToken` (max 4 pages).
- Page limit: 200 threads per window — above that, split the window.
- For each kept thread: `get_thread`.

## Fetch one item
- Gmail URL `…#all/thread-f:<n>` or a thread ID → `get_thread`.

## Filter
- Keep threads where at least one message is from a person (not an automated or list sender). Calendar invitations/RSVPs ("Invitation:", "Accepted:", "Declined:", "Updated invitation") are not human email — drop them (they're covered by Drive meeting notes).
- **Sensitive screen — skip entirely, do not capture:** HR cases, benefits, payroll,
  compensation/salary/offer letters, performance ratings, medical/leave, legal. Count only.

## Dedupe key
- ID: Gmail thread ID. Version: date of the newest message.
- Exit 2 (new messages): capture only the new messages as the next `-raw-vN.md`.

## Capture
- Path: `raw/email/YYYY-MM-DD-<subject-slug>-raw.md` (date of first message).
- Frontmatter: `type: raw-email`, `subject`, `from`, `to`, `date`, `thread-id`, `url`, `captured`.
- Body: per message oldest first: `### <Sender name> — YYYY-MM-DD HH:MM` then the text with
  quoted earlier replies removed.

## Compile
- Digest entry: "Email: <subject> from <sender>" with takeaways, asks to {{sage.owner.first_name}} (proposed
  `#todo/follow-up` to-dos with due dates), decisions, people/projects to touch.
- After OK: update people (fill `emails`), projects (`## Timeline`), decisions; to-dos go on
  the sender's person page `## Open threads` (or the project page if project-specific).
- Record: `mark gmail <threadId> <raw path> --version <newest message date>`.

## Mode
`digest`
