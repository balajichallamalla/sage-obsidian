---
type: page-type-spec
title: Page type — pr
---
# Page type: pr

**Folder:** `wiki/prs/`  
**File name:** `<repo>-<number>.md`  
**Purpose:** A GitHub pull request — summary and review context; GitHub is the record.  
**Template:** `_system/templates/pr.md`

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
| `repo` | yes | [[repo]] |
| `number` | yes | PR number |
| `url` | yes | PR URL |
| `author` | yes | [[person]] |
| `ticket` | yes | [[JIRA-KEY]] |

## Status values

`open`, `merged`, `closed`

## Body sections

In this order:

1. `## TL;DR` — 2–4 lines a reader can stop after.
2. `## What changed` — The change in 3–6 bullets.
3. `## Review notes` — Key feedback and how it was resolved.
4. `## Follow-ups` — Work spun out of this PR.
5. `## Related` — wikilinks to related pages.
6. `## Sources` — links into `raw/` or external URLs.

## Rules

- Use `[[wikilinks]]` for every person, project, repo, ticket, PR mention.
- Bump `updated:` on every edit.
- Every claim must trace to `sources:`.
- Conflicts: `> [!warning] Conflict` callout, never silent overwrite.
