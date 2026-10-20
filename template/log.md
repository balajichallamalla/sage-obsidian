---
type: log
title: Log
---
# Log

Append-only. Newest at the bottom. Every entry starts with `## [YYYY-MM-DD] <op> | <title>`.
Last 5 entries: `grep "^## \[" log.md | tail -5`

## [{{sage.setup_date}}] setup | Vault created by sage-obsidian {{sage.plugin_version}}
- Owner: {{sage.owner.name}} · preset: {{sage.preset}}
