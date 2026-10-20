---
type: workflow
title: Inbox triage
---
# Workflow: inbox (/inbox)

## Steps

1. Read the bullets under `## Inbox` in `inbox.md`. If empty, say so and stop.
2. Classify each item: to-do, thought/idea, meeting or 1:1 note, link/ticket/PR, question.
3. Present one table: item → proposed destination. Wait for {{sage.owner.first_name}}'s confirmation (one
   confirmation for the whole batch).
4. Apply:
   - **To-do** → checkbox with `#todo/<category>` + due date on the relevant project/person
     page, or today's `journal/YYYY-MM-DD.md` `## To-dos` (create from template if missing).
   - **Thought/idea, meeting, 1:1 note** → run the matching ingest workflow's capture + write
     steps (discussion already happened in step 3). Skip its Finish — step 6 covers it.
   - **Link / ticket / PR** → if its ingest workflow is a stub, add a to-do
     `- [ ] Ingest <link> #todo/review` to today's journal instead.
   - **Question** → answer via `query.md`.
5. Remove processed bullets from `inbox.md`; leave anything {{sage.owner.first_name}} deferred.
6. Update `index.md` for new pages, append `## [YYYY-MM-DD] inbox | triaged N items` to
   `log.md`, then `git add -A && git commit -m "inbox: triage N items"`.
