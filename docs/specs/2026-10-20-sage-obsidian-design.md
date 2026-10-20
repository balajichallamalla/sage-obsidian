---
type: spec
title: sage-obsidian plugin — design
status: approved
created: 2026-10-20
updated: 2026-10-20
---

# sage-obsidian — design

**What:** A Claude plugin that sets up a personal Obsidian "second brain" from scratch, the way Balaji's
vault works today: Karpathy-style LLM wiki (`raw/` captures → `wiki/` pages kept by Claude → schema in
`CLAUDE.md` + `_system/`), connector sync, Todoist sync, scheduled runs, weekly synthesis, meeting
prep and a command-center dashboard.

**Who:** Xometry engineers, managers, PMs and analysts first; every piece can be switched off, and
other people can build from it.

**Where:** source in `~/Desktop/Sage-obsidian`; Balaji pushes it to a Xometry GitHub repo for
testers; later, the Xometry Claude marketplace.

**Source of truth for behaviour:** Balaji's vault `~/Desktop/second-brain` (sub-projects 1–5). This
plugin generalises that framework; it never copies its content.

## 1. Decisions

| Topic | Decision |
|---|---|
| Audience | Xometry folks first: defaults tuned for Slack, Jira, Gmail, Drive/Gemini notes, GitHub PRs, 1:1s. |
| v1 modules | All: core (ingest, ask, search, lint, inbox, daily), connector sync, Todoist + schedules, weekly + prep + dashboard. Each is an on/off choice. |
| Engine location | Copied into the user's vault at setup (self-contained, customisable). Plugin skills route into the vault's own workflows. `/upgrade` brings new versions. |
| Existing vaults | v1 creates a new vault only; an old vault is left untouched (notes can be `/ingest`-ed later). |
| Packaging | Claude plugin + one-plugin marketplace in the same repo; installable in Claude Code and Cowork. |
| Credentials | None stored. Connectors are the user's own Claude account connectors. |
| Git | `git init` in the vault, local only — the generated `CLAUDE.md` forbids remotes. (The plugin repo itself is pushed by Balaji.) |

## 2. Repo layout

```
Sage-obsidian/
├── .claude-plugin/
│   ├── plugin.json            {"name": "sage-obsidian", "version": "0.1.0", "description", "author"}
│   └── marketplace.json       {"name": "sage-obsidian", "owner", "plugins": [{"name": "sage-obsidian", "source": "."}]}
├── skills/
│   ├── setup/SKILL.md         interview → config → render → git init → doctor → schedules
│   ├── doctor/SKILL.md        read-only health check
│   ├── upgrade/SKILL.md       new version → per-file diffs → migrations → commit
│   ├── help/SKILL.md          shows the vault's _system/HELP.md (or the README before setup)
│   └── ingest, sync, sync-status, ask, search, lint, inbox, daily,
│       todo-sync, weekly, prep, dash/SKILL.md      thin routers (§2.2)
├── template/                  generic vault framework with {{placeholders}} and module markers
├── presets/                   engineer.json, eng-manager.json, pm.json, data.json (default answers)
├── migrations/                NNN_<name>.py, run in order by /upgrade
├── scripts/
│   ├── render_vault.py        config + template → vault (idempotent)
│   ├── package.sh             builds dist/sage-obsidian.zip for Cowork upload
│   └── tests/                 render, leak, packaging tests (+ the template's own tool tests run from the rendered vault)
├── docs/                      connectors.md, customizing.md, troubleshooting.md, images/
├── README.md · CHANGELOG.md · LICENSE
```

No top-level `bin/` (Cowork refuses it). SKILL.md frontmatter uses only `name`, `description`
(and optionally `license`, `compatibility`, `metadata`, `allowed-tools`).

### 2.1 Install

- Claude Code: `/plugin marketplace add <org>/sage-obsidian` → `/plugin install sage-obsidian@sage-obsidian`.
- Cowork: Customize → Plugins → Add marketplace (same repo), or upload `dist/sage-obsidian.zip`.

### 2.2 Finding the vault

`/setup` writes `_system/config.json`. Every other skill looks for it in the current folder (Cowork
working folder or Claude Code cwd); if missing, it asks the user to open their vault folder (or run
`sage-obsidian:setup`) — it never guesses a path. Router skill body: read `CLAUDE.md` if not in
context → read `_system/workflows/<name>.md` → follow it with the arguments. A router whose module is
off says so and how to enable it (`/setup` change mode).

## 3. `/setup`

### 3.1 Interview (AskUserQuestion; a recommended answer pre-selected)

1. **You** — name; work email (from the account); role preset (Engineer, Eng manager, PM,
   Data/analytics); timezone.
2. **Vault** — folder (must be new or empty; default `~/Desktop/second-brain`, else `-2`); vault name.
3. **Modules** — sync sources (Slack, Jira, Gmail, Drive/Gemini meeting notes, GitHub PRs, Claude
   sessions), Todoist, scheduled runs (times), weekly + impact log, meeting prep, dashboard.
4. **Source details** (enabled modules only) — Jira site + project keys (default `MKTM`), Slack
   channels, Drive meeting-notes folder, Todoist project name, weekly hours target.

### 3.2 Connector check

For each chosen source, probe for its tools (ToolSearch). Present → fetch the user's IDs (Atlassian
cloudId + accountId, Slack user ID). Missing → show the connector to add (Cowork: connector
suggestion; Claude Code: exact steps), then: wait and re-check · skip for now (enable later) · turn
the module off.

### 3.3 Build

1. Write `_system/config.json` (§4).
2. `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/render_vault.py --config <config> --out <vault>`.
3. `git init`, first commit `setup: sage-obsidian v<version>`.
4. Run `/doctor`.
5. Offer: create the scheduled runs (Cowork `create_scheduled_task`, prompts reference the vault's
   workflows), install Dataview + Tasks, start a backfill.

### 3.4 Change mode

`/setup` in an existing vault: add/remove modules or sources, re-render framework files only (§6
rules), never touch notes.

## 4. `_system/config.json`

```json
{
  "schema_version": 1,
  "plugin_version": "0.1.0",
  "owner": {"name": "Jane Doe", "first_name": "Jane", "emails": ["jane.doe@xometry.com"],
            "match": ["jane", "jane doe", "jane.doe@xometry.com"], "timezone": "America/New_York"},
  "vault": {"name": "second-brain", "path": "/Users/jane/Desktop/second-brain"},
  "preset": "engineer",
  "modules": {"sync": true, "todoist": true, "schedules": true, "weekly": true, "prep": true, "dashboard": true},
  "sources": {
    "slack": {"enabled": true, "user_id": "U0EXAMPLE", "channels": ["#team"]},
    "jira": {"enabled": true, "site": "xometry.atlassian.net", "cloud_id": "<from setup>", "account_id": "<from setup>", "projects": ["MKTM"]},
    "gmail": {"enabled": true}, "drive_meetings": {"enabled": true, "folder": "Meet Recordings"},
    "github_prs": {"enabled": true}, "claude_sessions": {"enabled": true}
  },
  "todoist": {"project": "Work"},
  "schedules": {"morning": "30 8 * * 1-5", "end_of_day": "0 16 * * 1-5", "weekly": "0 15 * * 5"},
  "dashboard": {"hours_target": 40, "stale_hours": 12},
  "todo_categories": ["project", "follow-up", "review", "ticket", "idea", "growth"]
}
```

## 5. Template (from Balaji's vault, generalised)

- **Copied:** `CLAUDE.md`, `_system/` (workflows, page-types, templates, sources, tools, tests,
  dashboard, HELP.md, SETUP.md, normalize.md), `home.md`, `todos.md`, empty `inbox.md`, `index.md`
  (headings only), `log.md` (setup entry), `.obsidian/` (graph colours + filter, Dataview settings,
  daily notes; not plugin binaries), `.gitignore`.
- **Never copied:** `raw/`, `wiki/`, `journal/`, `_system/state/` contents, `specs/`, `plans/`, `.git`.
- **Generalised:** owner identity (tools read `config.json`: `week_facts.py` ME, `prep_context.py`
  ME_EMAILS, dashboard greeting / my-tickets / hours accountId, workflow prose); all IDs (cloudId,
  accountIds, Slack ID, Todoist IDs, project keys) come from config; preferences (schedule times,
  hours target, stale hours, to-do categories) are config defaults; `normalize.md` ships empty;
  sensitive-content rules always on.
- **Placeholders:** `{{owner.name}}`-style dotted paths into config. **Module blocks:**
  `<!-- module:todoist -->…<!-- /module -->` in markdown, `# module:todoist` … `# /module` in
  Python/JS; plus a manifest `template/modules.json` listing whole files per module.

## 6. `render_vault.py`

- Input: config + `template/` (+ `modules.json`). Output: vault folder.
- New vault: target must be empty or missing. Change mode (`--update`): writes framework files only
  (paths listed in `modules.json` + root framework files); deletes framework files of disabled
  modules; never touches `raw/`, `wiki/`, `journal/`, `inbox.md` content, or `_system/state/`.
- Unresolved placeholder → error naming file and key. Idempotent: same config twice → no changes.
- Stdlib only; runs in Cowork's sandbox and Claude Code.

## 7. `/doctor` (read-only)

Checks: config present and `schema_version` matches the plugin; enabled modules' files present;
Dataview (JS queries on) and Tasks installed (from `.obsidian/`; otherwise "check by hand"); each
enabled source's connector reachable (one cheap read); scheduled runs exist and are enabled; vault
validator passes; git clean; no stale run lock; pending digests. Output: one ✓/✗ line per check with
the fix. Runs at the end of `/setup` and `/upgrade`.

## 8. `/upgrade`

Render the new version from the user's config into a scratch folder → diff against framework files →
per changed file: show diff; if the user edited it, ask (take new · keep mine · merge by hand) → run
pending `migrations/` in order → bump `schema_version`/`plugin_version` → `/doctor` → one commit
`upgrade: vX → vY`. Never touches `raw/`, `wiki/`, `journal/`.

## 9. README.md

Pitch + hero dashboard screenshot · What you get (commands table) · Install (Claude Code, Cowork) ·
Set up in 5 minutes · Connectors (module → connector) · Daily use · Customizing (workflows, page
types, presets, adding a source) · Privacy & safety (local git, no remote, sensitive-content rules, no
API keys) · Upgrading · Troubleshooting (`/doctor`) · FAQ · Credits (Karpathy LLM Wiki, kepano
obsidian-skills). Deeper docs in `docs/`.

## 10. Testing

- Template tool tests (69 from the vault), updated to read the owner from config; run inside a
  rendered vault.
- `scripts/tests/test_render.py`: each preset × {all modules, minimal} renders; the rendered vault's
  `check_vault.py` passes; re-render with same config = no diff; disabling a module removes its files
  and routing rows; unresolved placeholder errors.
- `scripts/tests/test_leaks.py`: rendered vaults contain no `Balaji`, `challamalla`, his account/Slack
  IDs, cloudId or Todoist IDs, `MKTM-<digits>`; Xometry defaults allowed only in `presets/`.
- `scripts/tests/test_packaging.py`: manifests valid JSON with required fields; SKILL.md frontmatter
  keys ⊆ allowed six; no top-level `bin/`; every router skill has a matching template workflow.
- `claude plugin validate .` when the CLI is available.
- Live: Claude Code local install → `/setup` all modules into a test vault; Cowork zip upload →
  `/setup` minimal → `/doctor` all ✓.

## 11. Out of scope (v1)

Adopting existing vaults · non-Xometry connector presets beyond role defaults · marketplace listing ·
auto-update · Windows-specific paths.
