---
type: source
title: Source — Jira
---
# Source: jira

Connector: Atlassian (`searchJiraIssuesUsingJql`, `getJiraIssue`). `cloudId`:
`{{sage.sources.jira.cloud_id}}` (from `getAccessibleAtlassianResources`; the site URL was
rejected by the old connector). Working since 2026-10-19 via the newer Atlassian connector.
{{sage.owner.first_name}}'s Jira accountId: `{{sage.sources.jira.account_id}}`.

## Fetch window
- JQL dates are in {{sage.owner.first_name}}'s Jira time zone ({{sage.owner.timezone}}): convert START/END to
  `"YYYY-MM-DD HH:mm"` local.
- `searchJiraIssuesUsingJql` with
  `(assignee = currentUser() OR reporter = currentUser() OR watcher = currentUser()) AND updated >= "<START local>" AND updated < "<END local>" ORDER BY updated ASC`,
  `fields: ["summary","description","status","issuetype","priority","assignee","reporter","created","updated","project","labels","parent","comment"]`,
  `maxResults: 50`, `responseContentFormat: "markdown"`. Follow `nextPageToken` (max 4 pages).
- Results overflow easily: search with only `fields: ["summary","status","assignee","updated","parent"]`
  (`view: compact`), then `getJiraIssue` (`view: evidence`) per issue for description and
  comments — delegate that per-issue fetch to a subagent when there are more than ~10 issues.
- Page limit: 200 issues per window — above that, split the window.

## Fetch one item
- Key `ABC-123` or URL `…/browse/ABC-123` → `getJiraIssue` with the same fields.

## Filter
- Covered by the JQL. `watcher = currentUser()` stands in for "I commented" (commenting
  auto-watches). Mentions without a comment are a known gap.

## Dedupe key
- ID: issue key. Version: `fields.updated`.

## Capture
- None (link-only; Jira is the system of record).

## Compile
- **New** (`seen` exit 1): create `wiki/tickets/<KEY>.md` per `_system/page-types/ticket.md`:
  - frontmatter `key`, `url: https://{{sage.sources.jira.site}}/browse/<KEY>`, `status` = Jira
    status name, `assignee: "[[person]]"`, `project: "[[project]]"` when the parent epic, labels,
    or summary match an existing project's title/aliases (else blank), `sprint` if present.
  - TL;DR from summary + description (normalized); `## Why it matters`; `## Scope & acceptance`
    from acceptance criteria if present; `## Notes & progress` with dated bullets for the last
    5 comments (author, one-line gist).
  - If assignee is {{sage.owner.first_name}} and status is not Done: first line of `## Notes & progress` is
    `- [ ] <KEY>: <summary> #todo/ticket`.
  - Add `[[<KEY>]]` to the project's `tickets:` list and `## Timeline`, and to the assignee's
    person page `## Timeline`.
- **Changed** (`seen` exit 2): prepend a dated bullet to `## Notes & progress`
  (`- YYYY-MM-DD — status A → B; N new comments: <gist>`), update `status`; tick the
  `#todo/ticket` checkbox when status becomes Done.
- People: resolve assignee/reporter by `jira` account ID, then `emails`, then `aliases`; set the
  `jira` field when matched; unmatched → digest question, link name only.
- Record: `mark jira <KEY> wiki/tickets/<KEY>.md --version <updated>`.

## Mode
`auto`
