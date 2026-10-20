---
type: workflow
title: Query
---
# Workflow: query (/ask)

## Steps

1. Read `index.md`. Pick candidate pages from their one-line summaries.
2. Widen with search: `python3 _system/tools/search.py "<question keywords>" -n 10` (add
   `--type`, `--since`, `--person` when the question implies them; `--raw` only for exact
   quotes). Fall back to `grep -ril "<keyword>" wiki/ journal/` if the tool errors.
3. Read the candidate pages (follow wikilinks one hop if needed). Read `raw/` only when a wiki
   page is thin or you need an exact quote.
4. Answer with inline citations as `[[page]]`. Say plainly what the vault does not know.
   Choose the format that fits: prose, a table, a checklist, a timeline.
5. Offer to file the answer: "Save this as `wiki/syntheses/<slug>.md`?"
6. If {{sage.owner.first_name}} says yes: write the page per `_system/page-types/synthesis.md`, add it to
   `index.md` under `## Syntheses`, append
   `## [YYYY-MM-DD] query | <question>` to `log.md`, and
   `git add -A && git commit -m "query: <slug>"`.
7. If not filed, change nothing.
