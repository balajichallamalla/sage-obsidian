---
type: page-type-spec
title: Page type — repo
---
# Page type: repo

**Folder:** `wiki/repos/`  
**File name:** `<repo-name>.md`  
**Purpose:** A code repository: architecture and tribal knowledge.  
**Template:** `_system/templates/repo.md`

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
| `url` | yes | GitHub URL |
| `language` | yes | Primary language |
| `owners` | yes | [[person]] list |

## Status values

`active`, `archived`

## Body sections

In this order:

1. `## TL;DR` — 2–4 lines a reader can stop after.
2. `## Architecture` — Main modules and how data flows.
3. `## Conventions` — Patterns, naming, testing approach.
4. `## Gotchas` — Things that bite; known traps.
5. `## How to run & test` — Commands.
6. `## Related` — wikilinks to related pages.
7. `## Sources` — links into `raw/` or external URLs.

## Rules

- Use `[[wikilinks]]` for every person, project, repo, ticket, PR mention.
- Bump `updated:` on every edit.
- Every claim must trace to `sources:`.
- Conflicts: `> [!warning] Conflict` callout, never silent overwrite.
