---
type: page-type-spec
title: Page type — synthesis
---
# Page type: synthesis

**Folder:** `wiki/syntheses/`  
**File name:** `<slug>.md`  
**Purpose:** A saved answer, comparison, or analysis from /ask.  
**Template:** `_system/templates/synthesis.md`

## Frontmatter

| Field | Required | Notes |
|---|---|---|
| `type` | yes | Page type (fixed per folder) |
| `title` | yes | Human-readable title |
| `aliases` | yes | Alternate names so [[links]] resolve; check before creating pages |
| `tags` | yes | Free tags; to-do tags go on checkboxes, not here |
| `sources` | yes | Wikilinks into raw/ or external URLs this page is built from |
| `created` | yes | YYYY-MM-DD |
| `updated` | yes | YYYY-MM-DD — bump on every edit |
| `question` | yes | The question that produced this page |

## Status values

No `status` field for this type.

## Body sections

In this order:

1. `## TL;DR` — 2–4 lines a reader can stop after.
2. `## Answer` — The synthesised answer.
3. `## Evidence` — Bullets citing [[pages]].
4. `## Related` — wikilinks to related pages.
5. `## Sources` — links into `raw/` or external URLs.

## Rules

- Use `[[wikilinks]]` for every person, project, repo, ticket, PR mention.
- Bump `updated:` on every edit.
- Every claim must trace to `sources:`.
- Conflicts: `> [!warning] Conflict` callout, never silent overwrite.
