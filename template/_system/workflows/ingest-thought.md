---
type: workflow
title: Ingest — thought
---
# Workflow: ingest-thought

**Mode: Discuss first.** For brain dumps, ideas, reflections, and loose to-dos.

## Steps

1. **Capture.** If pasted, save verbatim to `raw/thoughts/YYYY-MM-DD-HHmm.md` with frontmatter
   `type: raw-thought`, `captured: YYYY-MM-DD`. Never edit it afterwards.
2. **Orient.** Read it. Read `index.md` for related ideas, projects, concepts, people.
3. **Discuss first.** Split the text into items and propose a destination for each, then
   wait for the user's reply before writing anything:
   - New idea → `wiki/ideas/<slug>.md` (status `seed`)
   - Adds to an existing idea / project / concept → which page and section
   - To-do → checkbox with `#todo/<category>` and due date, placed on the most relevant page
     (project page, person page, or today's `journal/YYYY-MM-DD.md` `## To-dos`)
   - Not worth filing → leave in raw only
4. Apply corrections.
5. Write/update pages as agreed. New pages follow `_system/page-types/<type>.md`;
   `sources:` links the raw file.
6. Run **Finish** from `_system/workflows/ingest.md` with type `thought`.
