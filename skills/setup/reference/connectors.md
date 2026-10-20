# Connector check

Probe each connector with ToolSearch (the query below); "present" means at least one matching tool
loads. Then fetch the IDs listed. Connectors are the user's own — never ask for tokens or API keys.

| Needed for | Connector | ToolSearch query | IDs to fetch → config |
|---|---|---|---|
| source slack, dashboard Slack inbox | Slack | `slack search` | the user's Slack user ID (search users by their email or read their own profile) → `sources.slack.user_id` |
| source jira, dashboard hours | Atlassian (Jira) | `jira atlassian` | `getAccessibleAtlassianResources` → cloud ID for the site → `sources.jira.cloud_id`; `atlassianUserInfo` → `account_id` |
| source gmail, source github_prs (Cowork) | Gmail | `gmail search threads` | none |
| source drive_meetings | Google Drive | `google drive search files` | none (folder name only) |
| meeting prep, dashboard calendar | Google Calendar | `calendar list events` | none |
| todoist | Todoist | `todoist find tasks` | none (the Work project and sections are created on the first `/todo-sync`) |
| source claude_sessions | Session history (Cowork) | `list sessions transcript` | none |
| source github_prs (Claude Code) | `gh` CLI | run `gh auth status` | none |

If a probe finds nothing, name the connector and where to add it (Cowork: Settings → Connectors, or
the connector suggestion tool; Claude Code: `claude mcp add` / the connectors page), then offer:
wait and re-check · skip for now · turn the module off.
