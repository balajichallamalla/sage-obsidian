---
name: doctor
description: "Read-only health check of a sage-obsidian vault: config and schema version, module files, Obsidian plugins, connectors, scheduled runs, validator, git, run lock, pending digests — each with the fix. Use for \"doctor\", \"is my vault ok\", \"something's broken\"."
---
# sage-obsidian doctor (read-only — change nothing)

1. **Find the vault**: the working folder must contain `_system/config.json`; otherwise ask the user
   to open their vault folder or run `sage-obsidian:setup`.
2. Run `python3 _system/tools/doctor.py` (file checks: config, modules, plugins, Dataview JS,
   validator, git, git remote, run lock, digests).
3. **Connectors** — for each source enabled in `config.sources` (and Calendar if prep or dashboard is
   on, Todoist if todoist is on): probe with ToolSearch (queries in the setup skill's
   `reference/connectors.md`) and make one cheap read (e.g. a 1-result search). ok / fail + where to
   reconnect.
4. **Schedules** — if `modules.schedules` is on and the scheduled-tasks tool exists: list tasks and
   check `vault-morning-sync`, `vault-end-of-day` (and `vault-weekly` if weekly is on) exist and are
   enabled.
5. **Plugin version** — compare `config.plugin_version` with this plugin's `.claude-plugin/plugin.json`
   version; older → suggest `sage-obsidian:upgrade`.
6. Print one checklist, ✓ / ⚠ / ✗ per line with the fix, then one line: "All good" or "N things to fix".
