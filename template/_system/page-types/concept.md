---
type: page-type-spec
title: Page type — concept
---
# Page type: concept

**Folder:** `wiki/concepts/`  
**File name:** `<concept-slug>.md`  
**Purpose:** Domain or technical knowledge; glossary terms.  
**Template:** `_system/templates/concept.md`

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

## Status values

No `status` field for this type.

## Body sections

In this order:

1. `## TL;DR` — 2–4 lines a reader can stop after.
2. `## Explanation` — Plain-language explanation.
3. `## How it applies here` — Where it shows up in {{sage.owner.first_name}}'s work.
4. `## Related` — wikilinks to related pages.
5. `## Sources` — links into `raw/` or external URLs.

## Rules

- Use `[[wikilinks]]` for every person, project, repo, ticket, PR mention.
- Bump `updated:` on every edit.
- Every claim must trace to `sources:`.
- Conflicts: `> [!warning] Conflict` callout, never silent overwrite.
