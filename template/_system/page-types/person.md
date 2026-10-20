---
type: page-type-spec
title: Page type — person
---
# Page type: person

**Folder:** `wiki/people/`  
**File name:** `firstname-lastname.md`  
**Purpose:** Someone {{sage.owner.first_name}} works with: manager, director, peer, report, stakeholder.  
**Template:** `_system/templates/person.md`

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
| `role` | yes | Job title |
| `team` | yes | Team / org |
| `relation` | yes | manager \| director \| peer \| report \| stakeholder |
| `emails` | yes | Work email addresses — first key for matching people across sources |
| `slack` | yes | Slack user ID, e.g. U0123456789 |
| `jira` | yes | Jira account ID |
| `github` | yes | GitHub login |

## Status values

`active`, `former`

## Body sections

In this order:

1. `## TL;DR` — 2–4 lines a reader can stop after.
2. `## Role & context` — What they own, what they care about.
3. `## Working with them` — Preferences, communication style, what lands well.
4. `## Open threads` — Things in flight between {{sage.owner.first_name}} and them.
5. `## Timeline` — Dated one-liners, newest first: `- 2026-10-18 — [[meeting]]: …`
6. `## Related` — wikilinks to related pages.
7. `## Sources` — links into `raw/` or external URLs.

## Rules

- Use `[[wikilinks]]` for every person, project, repo, ticket, PR mention.
- Bump `updated:` on every edit.
- Every claim must trace to `sources:`.
- Conflicts: `> [!warning] Conflict` callout, never silent overwrite.
