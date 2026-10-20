---
name: sync
description: "Pull new items from connectors (Slack, Jira, Gmail, Drive meeting notes, GitHub PRs, Claude sessions) into the sage-obsidian vault with one digest to review; supports --backfill. Use for \"sync my vault\"."
---
# sync

1. **Find the vault.** The current working folder must contain `_system/config.json` (a sage-obsidian
   vault). If it doesn't, ask the user to open their vault folder (Cowork: choose it as the working
   folder; Claude Code: `cd` into it) or to run `sage-obsidian:setup` to create one. Never guess a path.
2. If the vault's `CLAUDE.md` is not already in context, read it.
3. If `_system/workflows/sync.md` does not exist, the **sync** module is off in this vault: say so and
   that running `sage-obsidian:setup` again (change mode) turns it on. Stop.
4. Read `_system/workflows/sync.md` and follow it with the user's request and arguments.
5. Never add a git remote or push; never write secrets, compensation, health details or customer PII.
