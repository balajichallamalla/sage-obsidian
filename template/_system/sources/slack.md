---
type: source
title: Source — Slack
---
# Source: slack

Connector: Slack (`slack_search_public_and_private`, `slack_read_thread`, `slack_read_user_profile`).
{{sage.owner.first_name}}'s user ID: `{{sage.sources.slack.user_id}}`.

## Fetch window
- Convert START/END to Unix seconds.
- Search A (threads {{sage.owner.first_name}} posted in): `slack_search_public_and_private` with
  `filters: "from:<@{{sage.sources.slack.user_id}}>"`, `after: <START>`, `before: <END>`, `sort: "timestamp"`,
  `limit: 20`, `include_context: false`, `response_format: "detailed"` (concise omits channel IDs and ts); follow `cursor` (max 10 pages).
- Search B (mentions): same, with `keywords: ["<@{{sage.sources.slack.user_id}}>"]` and no `from:` filter (verified working 2026-10-19).
  If B returns 0 results for a window where A found messages, retry B with
  `filters: "with:<@{{sage.sources.slack.user_id}}>"` and note in the digest which query worked (then update this
  file so the working query is first).
- Group all hits by `channel_id` + thread root `ts` (a message's `thread_ts`, or its own `ts`
  when not threaded). For each group: `slack_read_thread`.
- Page limit: 200 messages across A+B per window — above that, split the window.

## Fetch one item
- Permalink `https://<team>.slack.com/archives/<CHANNEL>/p<TS16>` → `ts` = first 10 digits +
  `.` + last 6; if the URL has `thread_ts=`, use that as the root. `slack_read_thread`.

## Filter
- Drop bot-only threads, trivial chatter ("ok", "sure", "quick call?") and social threads.
- Un-threaded DMs: group one DM's substantive messages per day into one capture; ID `<dm_channel_id>:<YYYY-MM-DD>`.
- **Redact secrets at capture:** credential/paste links (privatebin, tokens, `sk=` share keys) → `[REDACTED — …]`.
- **Quiet rule:** if the latest reply is newer than 24 hours before now, skip the thread for
  this run (do not `mark` it); the next sync picks it up.
- Sensitive screen: threads about HR, payroll, compensation, health, legal → do not capture;
  count for the log.

## Dedupe key
- ID: `<channel_id>:<root_ts>`. Version: latest reply `ts`.
- Exit 2 (new replies, now quiet): capture only the new replies as the next `-raw-vN.md`.

## Capture
- Channel name via the search result; DMs as `dm-<other-person-slug>`; group DMs `mpdm-<slugs>`.
- Path: `raw/slack/YYYY-MM-DD-<channel>-<first-words-slug>-raw.md` (date of root message).
- Frontmatter: `type: raw-slack`, `channel`, `channel-id`, `thread-ts`, `permalink`,
  `participants: [<names>]`, `captured`.
- Body: one line per message `**<Name>** (YYYY-MM-DD HH:MM): <text>`, oldest first.

## Compile
- People: resolve participants by `slack` ID, then `emails` (`slack_read_user_profile`), then
  `aliases`; fill the `slack` field when matched.
- Update `## Timeline` / `## Current status` on projects discussed; add a decision page only
  when the thread states an explicit decision ("decided", "agreed", "going with").
- Asks directed at {{sage.owner.first_name}} that are still open → `- [ ] <ask> ([[slack-raw-file]]) #todo/follow-up`
  in the asker's person page `## Open threads`.
- Record: `mark slack <channel_id>:<root_ts> <raw path> --version <latest ts>`.

## Mode
`auto`
