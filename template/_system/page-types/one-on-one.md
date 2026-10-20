---
type: page-type-spec
title: Page type — one-on-one
---
# Page type: one-on-one

**Folder:** `wiki/one-on-ones/`  
**File name:** `1on1-<person-slug>.md`  
**Purpose:** ONE running page per 1:1 relationship. Newest session first.  
**Template:** `_system/templates/one-on-one.md`

## Frontmatter

| Field | Required | Notes |
|---|---|---|
| `type` | yes | Page type (fixed per folder) |
| `title` | yes | Human-readable title |
| `aliases` | yes | Alternate names so [[links]] resolve; check before creating pages |
| `status` | yes | See status values below |
| `tags` | yes | Free tags; to-do tags go on checkboxes, not here |
| `sources` | yes | Wikilinks into raw/ or external URLs this page is built from |
| `created` | yes | YYYY-MM-DD |
| `updated` | yes | YYYY-MM-DD — bump on every edit |
| `person` | yes | [[person]] |
| `cadence` | yes | weekly \| biweekly \| monthly |
| `last` | yes | YYYY-MM-DD of latest session |

## Status values

`active`, `ended`

## Body sections

In this order:

1. `## TL;DR` — 2–4 lines a reader can stop after.
2. `## Open threads` — Topics still in progress across sessions.
3. `## Feedback themes` — Recurring feedback, with dates.
4. `## My commitments` — {{sage.owner.first_name}}'s to-dos as checkboxes.
5. `## Their commitments` — What they said they'd do; plain bullets.
6. `## Session history` — `### YYYY-MM-DD` blocks, newest first, each linking its raw file.
7. `## Related` — wikilinks to related pages.
8. `## Sources` — links into `raw/` or external URLs.

## Rules

- Use `[[wikilinks]]` for every person, project, repo, ticket, PR mention.
- Bump `updated:` on every edit.
- Every claim must trace to `sources:`.
- Conflicts: `> [!warning] Conflict` callout, never silent overwrite.
