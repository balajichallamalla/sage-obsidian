---
type: source
title: Source — GitHub PRs
---
# Source: github-prs

No GitHub connector exists. Discovery: GitHub notification emails (Gmail). Details: `gh` CLI in
Claude Code; email content in Cowork. If a GitHub connector becomes available, replace only
this file's fetch sections.

## Fetch window
- Discovery (both apps): Gmail `search_threads` with
  `from:notifications@github.com after:<START_UNIX> before:<END_UNIX> (cc:review_requested@noreply.github.com OR cc:author@noreply.github.com)`,
  `pageSize: 50`; follow `nextPageToken` (max 4 pages). Parse subjects
  `[{{sage.sources.github_prs.org}}/<repo>] <title> (PR #<n>)` → `(repo, n)`; de-duplicate pairs.
- Discovery (Claude Code only, additionally):
  `gh search prs --author @me --owner {{sage.sources.github_prs.org}} --updated ">=<START date>" --json repository,number --limit 100`
  and `gh search prs --review-requested @me --owner {{sage.sources.github_prs.org}} --updated ">=<START date>" --json repository,number --limit 100`.
- Details — Claude Code: `gh pr view <n> -R {{sage.sources.github_prs.org}}/<repo> --json number,title,state,author,url,body,headRefName,reviewRequests,reviews,mergedAt,closedAt,createdAt`.
  Cowork: `get_thread` on the notification thread; take title, state hints ("merged",
  "closed"), author, requested reviewers, and the PR description from the first message.
- Page limit: 100 PRs per window — above that, split the window.

## Fetch one item
- URL `https://github.com/{{sage.sources.github_prs.org}}/<repo>/pull/<n>` → Claude Code `gh pr view`; Cowork: Gmail
  `search_threads` `from:notifications@github.com "(PR #<n>)" <repo>` then `get_thread`.

## Filter
- Owner `{{sage.sources.github_prs.org}}` only. Keep PRs authored by {{sage.owner.first_name}} or with {{sage.owner.first_name}}'s review requested. If the repo allowlist (`{{sage.sources.github_prs.repos}}`) is not empty, also require the repo to be on it **or** the title/branch to mention a ticket key from `{{sage.sources.jira.projects}}`.
- If discovery overflows (more than ~40 PRs/week), narrow the Gmail query with the allowlisted repo names and ticket keys.
  Drop bot authors (`dependabot`, `renovate`, `github-actions`).

## Dedupe key
- ID: `<repo>#<n>`. Version: state (`open` | `merged` | `closed`).

## Capture
- None (link-only; GitHub is the system of record).

## Compile
- **New:** `wiki/prs/<repo>-<n>.md` per `_system/page-types/pr.md`: `repo: "[[<repo>]]"`
  (create a minimal `wiki/repos/<repo>.md` with `url: https://github.com/{{sage.sources.github_prs.org}}/<repo>` if
  missing), `number`, `url`, `author: "[[person]]"` (match `github` login, then `emails`,
  `aliases`; fill `github` when matched), `ticket: "[[KEY]]"` from a `[A-Z]+-\d+` match in
  title or branch, `status` = state. TL;DR from title + description; `## What changed` 3–6
  bullets; `## Review notes` from reviews (Claude Code) or notification content (Cowork).
- Review requested from {{sage.owner.first_name}} and state `open`: first line of `## Review notes` is
  `- [ ] Review [[<repo>-<n>]] #todo/review`.
- Link back: add `[[<repo>-<n>]]` to the ticket page `## Notes & progress` and the repo page.
- **Changed:** dated bullet in `## Review notes` (`- YYYY-MM-DD — open → merged`), update
  `status`; tick the review to-do when merged/closed.
- Record: `mark github-prs <repo>#<n> wiki/prs/<repo>-<n>.md --version <state>`.

## Mode
`auto`
