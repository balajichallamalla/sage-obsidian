# Connectors

sage-obsidian never stores credentials. It uses the connectors already on your Claude account.

| Source | Connector | What is pulled | Mode |
|---|---|---|---|
| Slack | Slack | Your messages, mentions and DMs; threads you're in | auto-filed |
| Jira | Atlassian | Tickets assigned to / reported by / watched by you in your project keys | auto-filed |
| Gmail | Gmail | Emails from people to you (newsletters, notifications, HR/payroll/health skipped) | digest — you approve |
| Drive meeting notes | Google Drive | Gemini "Notes by Gemini" docs | digest — you approve |
| GitHub PRs | Gmail notifications (Cowork) or `gh` (Claude Code) | PRs you authored or were asked to review | auto-filed |
| Claude sessions | Session history (Cowork) | Substantive work sessions | auto-filed |
| Calendar | Google Calendar | Today's events for meeting prep and the dashboard | read only |
| Todoist | Todoist | Two-way to-do sync in one project with a section per category | two-way |

Add a missing connector in Cowork under **Settings → Connectors**, then re-run `sage-obsidian:setup`
in your vault (change mode) to switch the source on.
