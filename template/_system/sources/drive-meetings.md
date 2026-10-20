---
type: source
title: Source — Google Drive meeting notes (Gemini)
---
# Source: drive-meetings

Connector: Google Drive (`search_files`, `get_file_metadata`, `read_file_content`).

## Fetch window
- `search_files` with
  `title contains 'Notes by Gemini' and modifiedTime >= '<START>' and modifiedTime < '<END>'`,
  `pageSize: 50`, `excludeContentSnippets: true`. Follow `nextPageToken` (max 4 pages).
- Page limit: 100 files per window — above that, split the window.
- For each file: `read_file_content(fileId)`.

## Fetch one item
- From a Docs URL take the ID between `/d/` and the next `/`. `get_file_metadata` then
  `read_file_content`.

## Filter
- `mimeType` is `application/vnd.google-apps.document` and title contains `Notes by Gemini`.
- All accessible notes are in scope (owned or shared).

## Dedupe key
- ID: Drive `fileId`. Version: `modifiedTime`.
- `seen` exit 2 (changed): re-capture as the next `-raw-vN.md` only if `modifiedTime` is more
  than 1 hour after the version recorded; otherwise just `mark` the new version. Flag
  re-captures in the digest's Conflicts section.

## Capture
- Title format: `<Meeting name> - YYYY/MM/DD HH:MM TZ - Notes by Gemini`.
- Path: `raw/meetings/YYYY-MM-DD-<meeting-name-slug>-raw.md`.
- Frontmatter: `type: raw-meeting`, `title`, `date`, `attendees: [<names>]`,
  `source: <viewUrl>`, `drive-file-id`, `drive-modified`, `captured: YYYY-MM-DD`.
- Body: the Gemini **Full notes** section verbatim — `### Summary`, `### Decisions`,
  `### Next steps`, `### Details` — stopping at the `# Transcript` heading. The transcript is
  not captured (30–70k chars each); keep its Drive link in frontmatter (`transcript:`).
  Gemini survey/boilerplate lines are dropped. Never edit afterwards.
- Docs with no Gemini summary ("A summary wasn't produced…") are not captured; `mark` them
  with path `skipped`.
- Large docs: if `read_file_content` overflows, read the saved result file (summary and
  details come first) — the transcript tail is not needed.

## Compile
- Digest entry (meeting block) built from `_system/workflows/ingest-meeting.md` step 3.
- After {{sage.owner.first_name}}'s OK: `ingest-meeting.md` steps 5–9 (meeting page, people, projects, decisions,
  conflicts). Match attendees by `emails` first (mailto links in the notes), then `aliases`;
  add missing emails to existing person pages.
- Record: `mark drive-meetings <fileId> wiki/meetings/<file>.md --version <modifiedTime>`.

## Mode
`digest`
