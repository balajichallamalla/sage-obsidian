---
type: workflow
title: Dash
---
# Workflow: dash (/dash)

**Mode: automatic, read-only for the wiki.** Refreshes the command-center snapshot
`_system/state/dashboard.json` (git-ignored). No run lock, no wiki edits, no log entry, no commit —
safe to run any time, including during another run.

## Steps

Collect each source into one `part.json` in the scratch folder. If a source fails, put
`"errors": {"<source>": "<one-line reason>"}` instead of its key and keep going.

1. **calendar** — Google Calendar `list_events` for today (primary, `orderBy: startTime`).
   Drop events {{sage.owner.first_name}} declined, all-day events, and events with no other attendees. Each item:
   `{"start": "HH:MM", "end": "HH:MM", "title": "<summary>", "attendees": <count>, "url": "<htmlLink>"}`.
<!-- module:source:jira -->
2. **jira_worklogs** — Atlassian `searchJiraIssuesUsingJql` (cloudId
   `{{sage.sources.jira.cloud_id}}`) with
   `worklogAuthor = currentUser() AND worklogDate >= startOfWeek()` and fields
   `["summary", "worklog"]`. For every worklog: `{"key", "started", "seconds": timeSpentSeconds,
   "author_is_me": author.accountId == "{{sage.sources.jira.account_id}}"}`.
   If an issue reports more worklogs than returned, fetch the rest with `getJiraIssue`.
<!-- /module -->
<!-- module:source:slack -->
3. **slack** — last 3 days, using Slack search:
   - DMs and group DMs where the latest message is not from {{sage.owner.first_name}} → `kind: "dm"`.
   - Messages that @mention {{sage.owner.first_name}} with no later reply from him in that thread → `kind: "mention"`.
   - Threads he started or replied in with newer replies than his last message → `kind: "thread"`.
   Keep only items that ask {{sage.owner.first_name}} something or request an action (drop FYIs, thanks, reactions).
   Each item: `{"kind", "who", "where": "#channel or DM", "text": "<the ask, ≤140 chars>",
   "url": "<permalink>", "ts": "<ISO time>"}`. Never include secrets or HR/health content.
<!-- /module -->
<!-- module:source:github_prs -->
4. **prs** — review requests for {{sage.owner.first_name}} from the last 30 days: Gmail
   `from:notifications@github.com "requested your review"` and review-request messages in
   {{sage.sources.github_prs.review_channels}} (skip if none are configured). Drop PRs whose `wiki/prs/<repo>-<number>.md` page has `status: merged` or
   `closed`, or that GitHub email says were merged/closed. Each item:
   `{"repo", "number": <int>, "title", "author", "url", "requested": "YYYY-MM-DD"}`.
   (Claude Code with `gh`: `gh search prs --review-requested=@me --state=open` instead.)
<!-- /module -->
5. `python3 _system/tools/dash_snapshot.py write <part.json>` — exit 2 means the part was
   invalid: fix the item it names and re-run. Show its status lines to {{sage.owner.first_name}} in one short message.

## Scheduled runs

`vault-morning-sync` and `vault-end-of-day` run this workflow as their last step.
