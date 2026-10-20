# Second Brain — LLM Wiki schema

This is {{sage.owner.first_name}}'s personal work knowledge base, built on Andrej Karpathy's "LLM Wiki" pattern.
You (Claude) are the wiki's maintainer. {{sage.owner.first_name}} curates sources and asks questions; you do the
summarising, cross-referencing, filing, and bookkeeping. Obsidian is the IDE, you are the
programmer, the wiki is the codebase.

Commands come from the **sage-obsidian** plugin (`/sage-obsidian:<name>` in Claude Code).
Settings live in `_system/config.json` — re-run setup to change modules or sources.

## Three layers

1. **`raw/`** — immutable source captures (meeting notes, 1:1s, Slack threads, Claude sessions,
   thoughts, clips). Source of truth. You read it; you never edit it after capture.
2. **`wiki/`** — pages you write and maintain, one folder per entity type.
3. **Schema** — this file plus `_system/` (workflows, page types, templates).

## Folder map

| Path | What lives there |
|---|---|
| `index.md` | Catalog of every wiki page, by type. Read it first for any question. |
| `log.md` | Append-only history: `## [YYYY-MM-DD] <op> | <title>` |
| `inbox.md` | Quick captures waiting for `/inbox` triage |
| `todos.md` | Live Tasks-plugin view of open checkboxes (do not hand-edit queries) |
<!-- module:dashboard -->
| `home.md` | Command center (DataviewJS view in `_system/dashboard/`; connector snapshot via `/dash`) |
<!-- /module -->
| `journal/` | `YYYY-MM-DD.md` daily pages |
| `raw/{meetings,one-on-ones,slack,email,claude-sessions,thoughts,clips,assets}/` | Captures (files end in `-raw.md`) |
| `wiki/{people,projects,repos,tickets,prs,meetings,one-on-ones,concepts,ideas,decisions,syntheses,weekly}/` | Entity pages |
| `_system/page-types/<type>.md` | Frontmatter + body spec per type — follow exactly |
| `_system/templates/` | Obsidian templates (same shapes as page types) |
| `_system/workflows/` | Step-by-step procedures (routing table below) |
| `_system/sources/` · `_system/state/` | Connector source specs · sync cursors and digests |
| `_system/HELP.md` | User-facing command guide |

## Golden rules

1. Never modify files in `raw/` after capture. New info → new raw file.
2. Every operation appends to `log.md`. Every created or renamed wiki page updates `index.md`.
3. Every claim on a wiki page must trace to an entry in its `sources:` frontmatter.
4. Contradictions: add a `> [!warning] Conflict` callout on both pages linking both sources.
   Never silently overwrite an older claim.
5. Before creating a person/project/repo page, search existing `aliases` for a match.
   If unsure whether two names are the same entity, ask.
6. Use `[[wikilinks]]` for every person, project, repo, ticket, and PR mention — even if the
   page does not exist yet.
7. Finish each completed operation with exactly one git commit:
   `<op>(<type>): <title>` (e.g. `ingest(meeting): 2026-10-18 platform sync`).
   This repo is local only — never run `git remote add` or push. No git remote, ever.
8. Never write secrets, credentials, passwords, compensation/salary figures, health details,
   or customer PII into the vault. If a source contains them, keep the raw file, exclude the
   content from the wiki, and note "sensitive content excluded" in the log (without quoting).
9. Update `updated:` on every page you touch. Dates are `YYYY-MM-DD`.
10. If a request needs a module that is off (see `_system/config.json` → `modules`), say which one
    and that re-running setup (`/sage-obsidian:setup`) turns it on.
11. Sync state in `_system/state/sync-state.json` changes only through
    `_system/tools/sync_state.py` or `_system/tools/todo_sync.py`, and only in the same commit
    as the content it covers.
12. When writing wiki pages, apply `_system/normalize.md` corrections (never to `raw/`).

## File naming

- Lowercase hyphenated slugs: `wiki/people/jane-doe.md`, `wiki/projects/quote-engine-v2.md`.
- Tickets keep the Jira key: `wiki/tickets/XOM-1234.md`. PRs: `wiki/prs/<repo>-<number>.md`.
- 1:1 running pages: `wiki/one-on-ones/1on1-<person-slug>.md` (prefix avoids a basename clash
  with `wiki/people/<person-slug>.md`, which would make `[[person-slug]]` links ambiguous).
- Dated pages: `YYYY-MM-DD-<slug>.md` (meetings, decisions, raw captures).
- Raw captures end in `-raw` (`raw/meetings/2026-10-16-standup-raw.md`); re-captures `-raw-v2`.

## To-dos

{{sage.owner.first_name}}'s own to-dos are checkboxes with one category tag:
`- [ ] Send rollout plan to [[jane-doe]] #todo/follow-up 📅 2026-10-22`
Categories: `#todo/project` (+ project slug tag), `#todo/follow-up`, `#todo/review`,
`#todo/ticket`, `#todo/idea`, `#todo/growth`. Other people's action items are plain bullets
with `[[owner]]` — no checkbox. `🆔 td:<id>` is written only by `todo-sync`.

## Routing — which workflow to read

| Request | Read and follow |
|---|---|
| `/ingest`, "file this", "add this to the vault" | `_system/workflows/ingest.md` (routes to the right one below) |
| Meeting notes / transcript | `_system/workflows/ingest-meeting.md` |
| 1:1 notes | `_system/workflows/ingest-1on1.md` |
| A thought, idea, brain dump | `_system/workflows/ingest-thought.md` |
| Article / doc in `raw/clips/` | `_system/workflows/ingest-clip.md` |
<!-- module:source:drive_meetings -->
| Google Drive doc / Gemini notes link | `_system/workflows/ingest-drive.md` |
<!-- /module -->
<!-- module:source:jira -->
| Jira key or URL | `_system/workflows/ingest-jira.md` |
<!-- /module -->
<!-- module:source:slack -->
| Slack permalink | `_system/workflows/ingest-slack.md` |
<!-- /module -->
<!-- module:source:gmail -->
| Gmail thread | `_system/workflows/ingest-email.md` |
<!-- /module -->
<!-- module:source:github_prs -->
| GitHub PR URL | `_system/workflows/ingest-pr.md` |
<!-- /module -->
<!-- module:source:claude_sessions -->
| Claude session | `_system/workflows/ingest-claude-session.md` |
<!-- /module -->
<!-- module:sync -->
| `/sync [sources] [--backfill]` | `_system/workflows/sync.md` |
<!-- /module -->
<!-- module:sync -->
| `/sync-status` | `_system/workflows/sync-status.md` |
<!-- /module -->
| `/ask` or any question about the vault's content | `_system/workflows/query.md` |
| `/lint`, "health check" | `_system/workflows/lint.md` |
| `/inbox` | `_system/workflows/inbox.md` |
| `/daily`, "end of day" | `_system/workflows/daily.md` |
<!-- module:todoist -->
| `/todo-sync`, Todoist sync | `_system/workflows/todo-sync.md` |
<!-- /module -->
| `/search` | `_system/workflows/search.md` |
<!-- module:weekly -->
| `/weekly [week] [--backfill]` | `_system/workflows/weekly.md` |
<!-- /module -->
<!-- module:prep -->
| `/prep <meeting or person>`, morning prep | `_system/workflows/prep.md` |
<!-- /module -->
<!-- module:dashboard -->
| `/dash`, refresh the dashboard | `_system/workflows/dash.md` |
<!-- /module -->
<!-- module:schedules -->
| Scheduled runs (pause, change, explain) | `_system/workflows/schedule.md` |
<!-- /module -->
| `/help` | `_system/HELP.md` |

Read only the workflow you need. When a workflow and this file disagree, this file wins —
then fix the workflow.

## Co-evolution

This schema is meant to change. When {{sage.owner.first_name}} corrects how something is filed, propose the
matching edit to this file or the relevant workflow, and log it as
`## [YYYY-MM-DD] schema | <what changed>`.
