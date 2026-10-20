---
name: setup
description: "Create a new Obsidian second-brain vault kept by Claude (sage-obsidian): a short interview, connector checks, then the vault is built, git-initialised and health-checked. Also change mode: re-run inside an existing vault to add or remove modules and sources. Use for \"set up my second brain\", \"sage setup\", \"add Slack to my vault\"."
---
# sage-obsidian setup

You are setting up (or changing) a personal Obsidian vault that Claude maintains. Be brief and
friendly; use AskUserQuestion for every choice, with the recommended option first.

Plugin files: `${CLAUDE_PLUGIN_ROOT}` (scripts, presets, template). If that path is not visible to
the shell, find it: `find / -path '*sage-obsidian*/scripts/render_vault.py' 2>/dev/null | head -1`.
Call it `$P` below. Work in a scratch folder for `answers.json` / `config.json`.

## 0. Which mode?

- The working folder (or the folder the user names) contains `_system/config.json` → **change mode**
  (section 6).
- Otherwise → **new vault**. If the user has an existing Obsidian vault, do not touch it: create the
  new vault next to it; they can `/ingest` old notes later.

## 1. Interview (new vault)

Ask in four short rounds. Pre-fill what you can (name and email from the account/user context).

1. **You** — full name; work email; role preset (read `$P/presets/*.json` `label` + `description`:
   Engineer, Eng manager, PM, Data / analytics); timezone (default America/New_York).
2. **Vault** — folder (default `~/Desktop/second-brain`; if it exists and is not empty, propose
   `~/Desktop/second-brain-2`); vault name (default `second-brain`). In Cowork, request access to the
   parent folder with the directory tool first.
3. **Modules** (multi-select, preset defaults pre-selected) — Connector sync · Todoist sync · Scheduled
   runs · Weekly + impact log · Meeting prep · Dashboard. If sync is on: which sources (Slack, Jira,
   Gmail, Drive/Gemini meeting notes, GitHub PRs, Claude sessions).
4. **Details** (only for what's on) — Jira site (default xometry.atlassian.net) + project keys (e.g.
   MKTM); Slack channels worth watching; Drive meeting-notes folder; GitHub org (default xometry) +
   optional repo allowlist + PR review channels; Todoist project name (default Work); weekly hours
   target (default 40); schedule times (defaults 08:30 / 16:00 weekdays, Friday 15:00); how far back to
   backfill (default 8 weeks).

## 2. Connector check

For each needed connector, follow `reference/connectors.md`: probe with ToolSearch, then fetch the
user's IDs. Missing connector → tell the user exactly which one to add (Cowork: use the connector
suggestion tool if available; Claude Code: Settings → Connectors / `claude mcp`), then ask:
**Wait while I add it** (re-probe) · **Skip for now** (source stays off; enable later by re-running
setup) · **Turn this module off**.

## 3. Build

1. Write `answers.json` with only what you collected, e.g.
   `{"owner": {"name", "email", "timezone"}, "vault": {"name", "path"}, "modules": {...},
   "sources": {"slack": {"enabled", "user_id", "channels"}, "jira": {"enabled", "site", "cloud_id",
   "account_id", "projects"}, ...}, "todoist": {"project"}, "schedules": {...}, "dashboard": {"hours_target"},
   "sync": {"backfill_start": "YYYY-MM-DD"}}`.
2. `python3 $P/scripts/make_config.py --preset <preset> --answers answers.json --out config.json`
   (exit 2 names what's missing — ask for it).
3. Show a 6-line summary (owner, vault path, modules, sources, schedules) and ask **Create it?**
4. `python3 $P/scripts/render_vault.py --config config.json --out <vault path>`.
5. In the vault: `git init -q && git add -A && git commit -qm "setup: sage-obsidian v<version>"`.
   Never add a remote. (Cowork: if git leaves `*.lock` / `tmp_obj_*` files it can't delete, request
   delete permission for the folder, then `find .git \( -name 'tmp_obj_*' -o -name '*.lock' \) -delete`.)
6. Run the **doctor** skill steps (or `python3 _system/tools/doctor.py`).

## 4. Finish

Ask, one question each:
- **Scheduled runs** (if the module is on and the scheduled-tasks tool exists): create the tasks in
  `reference/schedules.md`, filling in the vault path and times. They run while the Claude app is
  open; a missed run happens at next launch — tell the user.
- **Obsidian**: open the folder as a vault (Obsidian → Open folder as vault), then install and enable
  **Dataview** and **Tasks** (Settings → Community plugins). The vault already ships Dataview's
  settings; toggle Dataview off/on once so it reads them.
- **First data** (if sync is on): start `/sync --backfill` now or later.

End with: the vault path, the 5 commands to try first (`/ingest`, `/ask`, `/sync`, `/daily`, `/dash`,
written as `/sage-obsidian:<name>` in Claude Code), and `/sage-obsidian:help`.

## 5. Rules

- One question at a time; never write outside the chosen vault folder and the scratch folder.
- Never store passwords, tokens or API keys. Connectors are the user's own Claude connectors.
- The vault is local-only git — never add a remote, never push.

## 6. Change mode (existing vault)

1. Read `_system/config.json`; show current modules and sources.
2. Ask what to add or remove (same choices as round 3–4); run the connector check for anything new.
3. Update the config: `python3 $P/scripts/make_config.py --preset <config.preset> --answers <changed
   fields merged into the old config> --out config.json`.
4. `python3 $P/scripts/render_vault.py --config config.json --out <vault> --update --dry-run`; show the
   files that will be written or removed; on **yes** run it without `--dry-run`. Notes in `raw/`,
   `wiki/`, `journal/` are never touched.
5. Commit `setup: modules <change>`; run doctor; create or delete scheduled tasks to match.
