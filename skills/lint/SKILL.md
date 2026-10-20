---
name: lint
description: "Health-check the sage-obsidian vault's content (broken links, orphans, stale pages, conflicts, overdue to-dos) and fix approved issues. Use for \"lint my vault\", \"health check my notes\"."
---
# lint

1. **Find the vault.** The current working folder must contain `_system/config.json` (a sage-obsidian
   vault). If it doesn't, ask the user to open their vault folder (Cowork: choose it as the working
   folder; Claude Code: `cd` into it) or to run `sage-obsidian:setup` to create one. Never guess a path.
2. If the vault's `CLAUDE.md` is not already in context, read it.
3. If `_system/workflows/lint.md` does not exist, the **core** module is off in this vault: say so and
   that running `sage-obsidian:setup` again (change mode) turns it on. Stop.
4. Read `_system/workflows/lint.md` and follow it with the user's request and arguments.
5. Never add a git remote or push; never write secrets, compensation, health details or customer PII.
