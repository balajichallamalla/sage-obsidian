---
type: page-type-spec
title: Page type — project
---
# Page type: project

**Folder:** `wiki/projects/`  
**File name:** `<project-slug>.md`  
**Purpose:** A body of work with a goal: initiative, feature, migration, epic.  
**Template:** `_system/templates/project.md`

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
| `owner` | yes | [[person]] |
| `repos` | yes | [[repo]] list |
| `tickets` | yes | [[JIRA-KEY]] list |
| `start` | yes | YYYY-MM-DD |
| `target` | yes | YYYY-MM-DD |

## Status values

`planned`, `active`, `paused`, `done`

## Body sections

In this order:

1. `## TL;DR` — 2–4 lines a reader can stop after.
2. `## Goals` — Why this exists; success criteria.
3. `## Current status` — 2–5 bullets, kept current.
4. `## Key decisions` — Links to [[decisions]].
5. `## Open questions` — Unresolved items.
6. `## Timeline` — Dated one-liners, newest first.
7. `## Related` — wikilinks to related pages.
8. `## Sources` — links into `raw/` or external URLs.

## Rules

- Use `[[wikilinks]]` for every person, project, repo, ticket, PR mention.
- Bump `updated:` on every edit.
- Every claim must trace to `sources:`.
- Conflicts: `> [!warning] Conflict` callout, never silent overwrite.
