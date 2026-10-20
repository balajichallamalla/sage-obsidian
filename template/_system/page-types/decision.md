---
type: page-type-spec
title: Page type — decision
---
# Page type: decision

**Folder:** `wiki/decisions/`  
**File name:** `YYYY-MM-DD-<slug>.md`  
**Purpose:** An ADR-style record of a significant decision.  
**Template:** `_system/templates/decision.md`

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
| `date` | yes | YYYY-MM-DD |
| `deciders` | yes | [[person]] list |
| `supersedes` | yes | [[decision]] this replaces, if any |

## Status values

`proposed`, `accepted`, `superseded`

## Body sections

In this order:

1. `## TL;DR` — 2–4 lines a reader can stop after.
2. `## Context` — What forced the decision.
3. `## Decision` — What was decided.
4. `## Alternatives considered` — And why not.
5. `## Consequences` — What this changes.
6. `## Related` — wikilinks to related pages.
7. `## Sources` — links into `raw/` or external URLs.

## Rules

- Use `[[wikilinks]]` for every person, project, repo, ticket, PR mention.
- Bump `updated:` on every edit.
- Every claim must trace to `sources:`.
- Conflicts: `> [!warning] Conflict` callout, never silent overwrite.
