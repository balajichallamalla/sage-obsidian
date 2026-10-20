---
type: workflow
title: Ingest — 1:1
---
# Workflow: ingest-1on1

**Mode: Discuss first.** 1:1s are sensitive — be conservative about what goes into the wiki.

## Steps

1. **Capture.** If pasted, save verbatim to `raw/one-on-ones/YYYY-MM-DD-<person-slug>.md` with
   frontmatter `type: raw-one-on-one`, `person`, `date`, `captured`. Never edit it afterwards.
2. **Orient.** Read the raw file, `wiki/one-on-ones/1on1-<person-slug>.md` (if any), and
   `wiki/people/<person-slug>.md`.
3. **Sensitive screen.** Compensation, ratings, health, personal matters, or anything said in
   confidence stay in `raw/` only. List what you will exclude (by category, not content).
4. **Discuss first.** Show {{sage.owner.first_name}}, then wait for the user's reply before writing anything:
   - Takeaways and feedback received
   - Open threads: new, progressed, closed
   - {{sage.owner.first_name}}'s commitments (proposed to-dos with `#todo/<category>` and due date)
   - Their commitments
   - Project/people pages that should be updated
   - The sensitive-exclusion list from step 3
5. Apply corrections.
6. Update (or create from `_system/templates/one-on-one.md`) `wiki/one-on-ones/1on1-<person-slug>.md`:
   - Add `### YYYY-MM-DD` at the top of `## Session history` with 3–6 bullets + link to raw file.
   - Refresh `## Open threads`, `## Feedback themes` (append dated line if a theme repeats).
   - Add checkboxes to `## My commitments`; plain bullets to `## Their commitments`.
   - Set `last:` to the session date.
7. Update `wiki/people/<person-slug>.md` `## Timeline` and `## Open threads`.
8. Update any project / idea / decision pages agreed in step 4.
9. If content was excluded, the log entry says `sensitive content excluded` (no details).
10. Run **Finish** from `_system/workflows/ingest.md` with type `1on1`.
