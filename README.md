# sage-obsidian

**A second brain that maintains itself.** Claude files your meetings, Slack threads, Jira tickets,
emails and PRs into an Obsidian wiki, keeps people/project/decision pages current, writes your weekly
impact summary, preps you for every meeting, and puts it all on one dashboard.

Built on Andrej Karpathy's *LLM Wiki* pattern: immutable **raw** captures → a **wiki** Claude
maintains → a **schema** (`CLAUDE.md`) that tells Claude how. Plain Markdown, local git, yours.

---

## What you get

| Command | What it does |
|---|---|
| `setup` | Interview → connector check → builds your vault (≈5 min). Re-run to add/remove modules. |
| `ingest` | File anything: meeting notes, 1:1s, thoughts, clips, a Jira key, a Slack/Gmail/Drive/GitHub link |
| `ask` · `search` | Answers with `[[citations]]` · ranked page search |
| `sync` · `sync-status` | Pull Slack, Jira, Gmail, Drive meeting notes, GitHub PRs, Claude sessions — one digest to review; `--backfill` for history |
| `daily` · `inbox` · `lint` | Journal page · triage quick captures · vault health |
| `todo-sync` | Two-way sync of `#todo/` checkboxes with Todoist |
| `weekly` | Week page (shipped, decisions, progress, blockers, next week) + running **impact log** |
| `prep` | Meeting brief: last time, what you owe, what they owe, open questions |
| `dash` | Refresh the **command center**: meetings, to-dos, Slack asks, PRs to review, ticket board, Jira hours |
| `doctor` · `upgrade` · `help` | Health check with fixes · bring your vault to the new version · guide |

In Claude Code commands are `/sage-obsidian:<command>`; in Cowork pick the skill or just ask
("sync my vault").

## Install

> The repo is **private** for now. Ask Balaji to add you as a collaborator first, and make sure
> you're signed in to GitHub (Claude Code uses your local `git` credentials; Cowork uses your
> connected GitHub account).

**Claude Code**
```
/plugin marketplace add balajichallamalla/sage-obsidian
/plugin install sage-obsidian@sage-obsidian
```
Or in one step: `/plugin install sage-obsidian --marketplace balajichallamalla/sage-obsidian`.
Update later with `/plugin marketplace update sage-obsidian`.

**Claude Cowork / claude.ai**
1. Customize → Plugins → **Add marketplace** → `balajichallamalla/sage-obsidian`
2. Install **sage-obsidian** from that marketplace.

If adding the private marketplace fails, use **Upload plugin** with `sage-obsidian.zip` instead:
download it from the repo's Releases page or build it with `scripts/package.sh` (it lands in
`dist/sage-obsidian.zip`).

**Check it worked:** run `sage-obsidian:help` — it explains what to do next.

## Set up in 5 minutes

1. Run **`sage-obsidian:setup`** and answer four short rounds: you · vault folder · modules · details.
2. Add any connectors it asks for (Settings → Connectors), or skip them for now.
3. Open the folder in Obsidian (**Open folder as vault**), then install and enable the **Dataview**
   and **Tasks** community plugins.
4. Run **`sage-obsidian:doctor`** — everything should be ✓.
5. Try `ingest` with today's meeting notes, then `ask` a question about them.

## Modules and connectors

| Module | Needs |
|---|---|
| Core (ingest, ask, search, lint, inbox, daily) | nothing |
| Connector sync | the connectors for the sources you pick: Slack · Atlassian (Jira) · Gmail · Google Drive · session history (Claude sessions); GitHub PRs via Gmail notifications (Cowork) or `gh` (Claude Code) |
| Todoist | Todoist connector |
| Scheduled runs | Cowork scheduled tasks (08:30 / 16:00 weekdays, Friday 15:00 — adjustable) |
| Weekly + impact log | nothing |
| Meeting prep · Dashboard | Google Calendar (dashboard also uses Slack, Jira, Gmail when on) |

Presets: **Engineer**, **Eng manager**, **PM**, **Data / analytics** — they only change the defaults.
Details: [docs/connectors.md](docs/connectors.md).

## Daily use

- Morning (automatic at 08:30): sync, to-dos, meeting briefs in your journal, dashboard refresh.
  Meetings and emails wait in a digest until you reply `ok`.
- During the day: `ingest` notes, `ask` questions, add to-dos from the dashboard.
- 16:00 (automatic): journal + to-do sync. Friday 15:00: weekly page + impact log.

## Customizing

Everything Claude follows lives in your vault as Markdown: `CLAUDE.md` (rules), `_system/workflows/`
(procedures), `_system/page-types/` (page shapes), `_system/sources/` (per-connector specs),
`_system/dashboard/` (the command center). Edit them freely — `upgrade` shows a diff and asks before
replacing anything you changed. See [docs/customizing.md](docs/customizing.md).

## Privacy and safety

- **Local only**: plain files + local git. Setup never adds a git remote; `doctor` flags one.
- **No credentials**: connectors are your own Claude connectors; nothing stores tokens or API keys.
- **Sensitive content stays out of the wiki**: compensation, health, HR, secrets and customer PII are
  kept only in `raw/` (or skipped) and logged as "sensitive content excluded".
- **Reviewable**: one commit per operation, an append-only `log.md`, and digests you approve before
  meeting notes or emails are filed.
- Don't turn on Obsidian Sync/iCloud for a vault with company-confidential notes.

## Upgrading

Update the plugin, open your vault, run **`sage-obsidian:upgrade`**. Your notes (`raw/`, `wiki/`,
`journal/`) are never touched.

## Troubleshooting

Run **`sage-obsidian:doctor`** first — every ✗ comes with its fix. More in
[docs/troubleshooting.md](docs/troubleshooting.md).

## FAQ

- **I already have a vault.** Setup creates a new one next to it; `ingest` old notes when useful.
- **Do I need every connector?** No — every module and source is optional.
- **Does it run when Claude is closed?** Scheduled runs need the Claude desktop app open; a missed run
  happens at next launch and the sync cursors catch up.

## Development

```
python3 -m unittest discover -s scripts/tests     # render, packaging, leak tests
scripts/package.sh                                 # builds dist/sage-obsidian.zip
```
Maintainers can re-import improvements from a working vault with `scripts/dev/import_vault.sh <vault>`
(needs a local, git-ignored `scripts/dev/identity.local.json`; see `identity.example.json`).

## Credits

[Andrej Karpathy — LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) ·
[kepano/obsidian-skills](https://github.com/kepano/obsidian-skills) for Obsidian syntax ·
built by Balaji Challamalla.
