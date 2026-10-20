---
type: workflow
title: Ingest — meeting
---
# Workflow: ingest-meeting

**Mode: Discuss first.** Do not write wiki pages until {{sage.owner.first_name}} confirms.

## Steps

1. **Capture.** If the input is pasted text, save it verbatim to
   `raw/meetings/YYYY-MM-DD-<slug>.md` with frontmatter:
   `type: raw-meeting`, `date`, `attendees: []`, `captured: YYYY-MM-DD`. Never edit it afterwards.
2. **Orient.** Read the raw file. Read `index.md` and find existing pages for attendees,
   projects, repos, tickets mentioned (match on `aliases` too).
3. **Discuss first.** Show {{sage.owner.first_name}}, then wait for the user's reply before writing anything:
   - 3–6 key takeaways
   - Decisions made (and which deserve a `wiki/decisions/` page)
   - Proposed to-dos for {{sage.owner.first_name}}: text, `#todo/<category>`, due date
   - Others' action items with owners
   - Pages to create / pages to update
   - Anything that contradicts existing wiki pages
4. Apply {{sage.owner.first_name}}'s corrections.
5. Write `wiki/meetings/YYYY-MM-DD-<slug>.md` per `_system/page-types/meeting.md`.
   `sources:` links the raw file. {{sage.owner.first_name}}'s to-dos go in `## Action items` as checkboxes.
   If `journal/<meeting date>.md` has a `## Meeting prep` brief for this meeting, link it in
   `## Related`: `[[journal/YYYY-MM-DD#Meeting prep]]`.
6. For each attendee: create or update `wiki/people/<slug>.md`; add a `## Timeline` line
   `- YYYY-MM-DD — [[meeting-slug]]: <their key point>`.
7. For each project / repo / ticket mentioned: update its page (`## Current status`,
   `## Timeline`, or `## Notes & progress`), or create a minimal page (frontmatter, TL;DR,
   Sources) if none exists.
8. For each accepted significant decision: create `wiki/decisions/YYYY-MM-DD-<slug>.md`.
9. Contradictions: `> [!warning] Conflict` callout on both pages.
10. Run **Finish** from `_system/workflows/ingest.md` with type `meeting`.
