---
type: page-type-spec
title: Page type — idea
---
# Page type: idea

**Folder:** `wiki/ideas/`  
**File name:** `<idea-slug>.md`  
**Purpose:** An idea or proposal, tracked from seed to outcome.  
**Template:** `_system/templates/idea.md`

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
| `origin` | yes | Where it came from: [[raw/thoughts/…]] or [[meeting]] |
| `effort` | yes | S \| M \| L |
| `impact` | yes | low \| medium \| high |

## Status values

`seed`, `exploring`, `proposed`, `adopted`, `dropped`

## Body sections

In this order:

1. `## TL;DR` — 2–4 lines a reader can stop after.
2. `## Problem` — What pain this addresses.
3. `## Proposal` — The idea.
4. `## Open questions` — What needs answering.
5. `## Next steps` — Checkboxes with #todo/idea.
6. `## Related` — wikilinks to related pages.
7. `## Sources` — links into `raw/` or external URLs.

## Rules

- Use `[[wikilinks]]` for every person, project, repo, ticket, PR mention.
- Bump `updated:` on every edit.
- Every claim must trace to `sources:`.
- Conflicts: `> [!warning] Conflict` callout, never silent overwrite.
