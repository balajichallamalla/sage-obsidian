---
type: workflow
title: Ingest (router)
---
# Workflow: ingest (router)

Entry point for `/ingest`. Picks the specific workflow, and defines the shared **Finish** and
**Failure** steps every ingest uses.

## Inputs

A path inside the vault (usually under `raw/`), pasted text, a URL, a Jira key, or a PR link.

## Steps

1. Classify the input with the first matching rule:

   | Signal | Workflow | Mode |
   |---|---|---|
   | Path in `raw/meetings/`, or notes/transcript of a meeting with 3+ people | `ingest-meeting.md` | discuss first |
   | Path in `raw/one-on-ones/`, or notes from a 1:1 with one named person | `ingest-1on1.md` | discuss first |
   | Path in `raw/thoughts/`, or a personal note, idea, brain dump, or to-do list | `ingest-thought.md` | discuss first |
   | Path in `raw/clips/`, or an article / external doc | `ingest-clip.md` | automatic |
   | Google Drive doc URL or file ID (Gemini "Notes by Gemini") | `ingest-drive.md` | discuss first |
   | Gmail thread link or thread ID | `ingest-email.md` | discuss first |
   | Jira key (`ABC-123`) or Jira URL | `ingest-jira.md` | automatic |
   | GitHub PR URL | `ingest-pr.md` | automatic |
   | Slack permalink or pasted Slack thread | `ingest-slack.md` | automatic |
   | Claude session export or memory file | `ingest-claude-session.md` | automatic |

2. If nothing matches, or two rules match equally, ask {{sage.owner.first_name}} which type it is. If no workflow
   fits, offer to draft a new `ingest-<type>.md` (and log it as a schema change).
3. If the chosen workflow says "Not implemented yet", tell {{sage.owner.first_name}} which sub-project owns it.
   If the input is pasted text, offer the fallback: save it to `raw/thoughts/` with a line
   `original-type: <type>` in its frontmatter and run `ingest-thought.md`.
4. Open the chosen workflow and follow it. It ends by running **Finish** below.

## Finish

Run after the specific workflow has written its wiki pages.

1. Bump `updated:` on every wiki page touched.
2. In `index.md`, add or refresh one line per created/renamed page under its type heading:
   `- [[slug]] — one-line summary`. Keep each section sorted alphabetically.
3. Append to `log.md`:
   ```
   ## [YYYY-MM-DD] ingest | <title>
   - created: [[a]], [[b]]
   - updated: [[c]], [[d]]
   - to-dos: N added
   - conflicts: none | [[x]]
   ```
4. Commit once: `git add -A && git commit -m "ingest(<type>): <title>"`.
5. Reply with: pages created, pages updated, to-dos added, conflicts flagged.

## Failure

If anything fails before Finish step 4: do **not** commit. List every file you touched and tell
{{sage.owner.first_name}} to review with `git diff` and either ask you to finish, or revert with
`git checkout -- <path>` (new files: `git clean -n` then `git clean -f <path>`).
