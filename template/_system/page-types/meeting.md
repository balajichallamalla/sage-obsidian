---
type: page-type-spec
title: Page type — meeting
---
# Page type: meeting

**Folder:** `wiki/meetings/`  
**File name:** `YYYY-MM-DD-<slug>.md`  
**Purpose:** Compiled summary of one meeting (raw notes stay in raw/meetings/).  
**Template:** `_system/templates/meeting.md`

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
| `date` | yes | YYYY-MM-DD |
| `attendees` | yes | [[person]] list |
| `project` | yes | [[project]] if any |

## Status values

No `status` field for this type.

## Body sections

In this order:

1. `## TL;DR` — 2–4 lines a reader can stop after.
2. `## Discussion` — Key points by topic.
3. `## Decisions` — Each linked to a [[decision]] page when significant.
4. `## Action items` — {{sage.owner.first_name}}'s as `- [ ] … #todo/<cat>`; others' as plain bullets with [[owner]].
5. `## Related` — wikilinks to related pages.
6. `## Sources` — links into `raw/` or external URLs.

## Rules

- Use `[[wikilinks]]` for every person, project, repo, ticket, PR mention.
- Bump `updated:` on every edit.
- Every claim must trace to `sources:`.
- Conflicts: `> [!warning] Conflict` callout, never silent overwrite.
