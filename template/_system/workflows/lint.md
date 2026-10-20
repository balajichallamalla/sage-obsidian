---
type: workflow
title: Lint
---
# Workflow: lint (health check)

Report first; fix only what {{sage.owner.first_name}} approves.

## Steps

1. Run the structural validator: `python3 _system/tests/check_vault.py` — include any FAIL lines.
2. Collect the content checks (use `grep`/`find`; list file paths):
   - **Broken links / missing pages:** every `[[target]]` in `wiki/` and `journal/` with no
     matching `target.md` anywhere. Rank by number of mentions — top ones are pages to create.
   - **Orphans:** pages in `wiki/` that no other page links to.
   - **Index drift:** wiki pages not listed in `index.md`; index lines pointing to missing pages.
   - **Frontmatter gaps:** pages missing fields required by `_system/page-types/<type>.md`.
   - **Stale:** pages with `status` in (active, open, exploring, In Progress) and `updated`
     older than 60 days.
   - **Open conflicts:** `grep -rl "\[!warning\] Conflict" wiki/`.
   - **Thin pages:** pages whose body is only a TL;DR.
   - **Overdue to-dos:** unchecked `- [ ]` with `📅` date before today.
   - **Stray root notes:** `*.md` files at the vault root other than `CLAUDE.md`, `index.md`,
     `log.md`, `inbox.md`, `todos.md`, `home.md` (usually created by clicking an unresolved link in
     Obsidian). Propose moving each into the right `wiki/` folder as a proper page.
3. Present a report grouped by check, each with counts and the top items. Suggest 3–5
   questions or sources worth investigating next.
4. Wait for {{sage.owner.first_name}} to choose which fixes to apply. Apply them.
5. Append `## [YYYY-MM-DD] lint | <N> issues, <M> fixed` to `log.md`.
6. If anything changed: `git add -A && git commit -m "lint: <summary>"`.
