---
type: page-type-spec
title: Page type — weekly
---
# Page type: weekly

**Folder:** `wiki/weekly/`  
**File name:** `YYYY-Www.md (ISO week, e.g. 2026-W43.md)`  
**Purpose:** One page per ISO week, written by /weekly from week_facts.py output only.  
**Template:** `_system/templates/weekly.md`

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
| `week` | yes | ISO week, e.g. 2026-W43 |
| `start` | yes | Monday, YYYY-MM-DD |
| `end` | yes | Sunday, YYYY-MM-DD |

## Status values

No `status` field for this type.

## Body sections

In this order:

1. `## TL;DR` — 2–4 lines a reader can stop after.
2. `## Shipped` — Merged PRs, closed tickets, tools/agents shipped — `[[link]] — what (date)`.
3. `## Decisions` — Decision pages dated this week.
4. `## Progress by project` — One line per project with timeline activity this week.
5. `## Open loops & blockers` — Blocked tickets, overdue to-dos, pending digests.
6. `## Next week` — Open to-dos due next week; {{sage.owner.first_name}}'s tickets in progress.
7. `## Numbers` — Meetings filed, pages created/updated, to-dos done/added.
8. `## Related` — wikilinks to related pages.
9. `## Sources` — links into `raw/` or external URLs.

## Rules

- Use `[[wikilinks]]` for every person, project, repo, ticket, PR mention.
- Bump `updated:` on every edit.
- Every claim must trace to `sources:`.
- Conflicts: `> [!warning] Conflict` callout, never silent overwrite.
