---
name: upgrade
description: "Bring a sage-obsidian vault's framework (workflows, tools, page types, dashboard, CLAUDE.md) up to the installed plugin version: per-file diffs, keeps the user's edits on request, runs migrations, never touches notes. Use for \"upgrade my vault\", after updating the plugin."
---
# sage-obsidian upgrade

`$P` = `${CLAUDE_PLUGIN_ROOT}` (if not visible to the shell:
`find / -path '*sage-obsidian*/scripts/render_vault.py' 2>/dev/null | head -1`, two levels up).

1. **Find the vault** (`_system/config.json` in the working folder). Take the run lock:
   `python3 _system/tools/run_lock.py acquire --owner upgrade` (exit 3 → stop and report).
2. Versions: `config.plugin_version` vs `$P/.claude-plugin/plugin.json`. Same → say "already up to
   date", release the lock, stop. Require a clean `git status` first (ask the user to commit or stash).
3. Copy `_system/config.json` to scratch, set `plugin_version` to the new version, then render the new
   framework into a scratch folder:
   `python3 $P/scripts/render_vault.py --config <scratch config> --out <scratch>/new`.
4. Compare: for each file in `<scratch>/new/_system/.framework-manifest.json`, the vault's
   `_system/.framework-manifest.json` hash tells whether the user edited it (current file hash ≠
   recorded hash).
   - Unchanged by the user → overwrite with the new file.
   - Edited by the user and the new version differs → show a short diff and ask: **take new** ·
     **keep mine** · **merge by hand** (write the new file next to it as `<name>.new` and say so).
   - New files → add. Files no longer in the new manifest → delete only if unedited; otherwise ask.
   Never touch `raw/`, `wiki/`, `journal/`, `inbox.md`, `index.md`, `log.md`, `_system/state/`.
5. Migrations: run every `$P/migrations/NNN_*.py` whose number is above `config.schema_version`, in
   order, with the vault as working directory; then set `schema_version` to the last one.
6. Write the new `_system/.framework-manifest.json` (from scratch/new) and the new `plugin_version`.
7. Run the doctor skill. Append `## [YYYY-MM-DD] upgrade | vX → vY` to `log.md` (list kept and merged
   files), commit `upgrade: vX → vY`, release the lock.
