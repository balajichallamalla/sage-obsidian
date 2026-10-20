---
type: page-type-spec
title: Page type — ticket
---
# Page type: ticket

**Folder:** `wiki/tickets/`  
**File name:** `<JIRA-KEY>.md`  
**Purpose:** A Jira work item — summary and context only; Jira is the system of record.  
**Template:** `_system/templates/ticket.md`

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
| `key` | yes | Jira key, e.g. XOM-1234 |
| `url` | yes | Jira URL |
| `project` | yes | [[project]] |
| `assignee` | yes | [[person]] |
| `sprint` | yes | Sprint name |

## Status values

`mirrors Jira status (e.g. To Do, In Progress, In Review, Done)`

## Body sections

In this order:

1. `## TL;DR` — 2–4 lines a reader can stop after.
2. `## Why it matters` — Business/tech reason.
3. `## Scope & acceptance` — What done means.
4. `## Notes & progress` — Dated notes, newest first.
5. `## Related` — wikilinks to related pages.
6. `## Sources` — links into `raw/` or external URLs.

## Rules

- Use `[[wikilinks]]` for every person, project, repo, ticket, PR mention.
- Bump `updated:` on every edit.
- Every claim must trace to `sources:`.
- Conflicts: `> [!warning] Conflict` callout, never silent overwrite.
