---
type: source
title: Source — Claude sessions
---
# Source: claude-sessions

Cowork: `session_info` tools (`list_sessions`, `read_transcript`). Claude Code: also
`~/.claude/projects/*/*.jsonl`.

## Fetch window
- Cowork: `list_sessions` with `limit: 100`. Candidates: `is_child: false`, status idle, not the
  current session, title not in the skip list. `read_transcript` each candidate; keep it if its
  last message time is within `[START, END)`.
- Claude Code (additionally):
  `find ~/.claude/projects -name '*.jsonl' -newermt '<START>' ! -newermt '<END>'`.
- Skip list (case-insensitive title contains): `Morning brief`.
- Page limit: 40 sessions per window — above that, split the window.

## Fetch one item
- Cowork session ID (`local_…`) → `read_transcript`; Claude Code `.jsonl` path → read the file.

## Filter
- At least 3 user turns. Skip sessions that only ran a scheduled/routine task, tool/skill listings, connector setup, or one-off personal message rewording.
- Sensitive screen as in CLAUDE.md rule 8 (exclude from wiki; raw keeps the export).

## Dedupe key
- ID: session ID (Cowork `local_…` or Claude Code file UUID). Version: last message timestamp.
- Exit 2 (session continued): capture only the new turns as the next `-raw-vN.md`.

## Capture
- Path: `raw/claude-sessions/YYYY-MM-DD-<title-slug>-raw.md` (date of first message).
- Frontmatter: `type: raw-claude-session`, `session-id`, `title`, `app: cowork|claude-code`,
  `project` (cwd or repo), `started`, `last-active`, `captured`.
- Body (**outcome export**, chosen 2026-10-19): `read_transcript` with `limit: 8`; keep {{sage.owner.first_name}}'s last asks and Claude's final answers only. Cowork transcripts carry no timestamps → window filtering is impossible; rely on `seen` (version = transcript message count/last answer hash). For each turn kept, `### {{sage.owner.first_name}}` + the user message, then `### Claude (final)` + the last
  assistant text of that turn. Tool calls and tool results are removed. Any single message
  longer than 4000 characters is cut with `[…truncated N chars]`.

## Compile
- Repo knowledge → `wiki/repos/<repo>.md` (`## Conventions`, `## Gotchas`, `## How to run & test`).
- Domain/tech knowledge → `wiki/concepts/`.
- Explicit decisions → `wiki/decisions/`; project progress → project `## Timeline`.
- Ticket keys mentioned (`PROJ-123`) → link `[[PROJ-123]]`; add a dated bullet on the ticket
  page if it exists.
- To-dos only when the session states a next step for {{sage.owner.first_name}}: `#todo/project`.
- Record: `mark claude-sessions <session id> <raw path> --version <last message timestamp>`.

## Mode
`auto`
