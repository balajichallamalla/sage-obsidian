---
type: workflow
title: Ingest — Jira
---
# Workflow: ingest-jira

Targeted ingest of one Jira issue. **Mode: automatic.**

## Steps

1. Read `_system/sources/jira.md`. Follow `## Fetch one item`, then
   `python3 _system/tools/sync_state.py seen jira <KEY> --version <updated>` (exit 0 → already
   current; say so and stop), then `## Compile` (new or changed path).
2. `python3 _system/tools/sync_state.py mark jira <KEY> wiki/tickets/<KEY>.md --version <updated>`.
3. Run **Finish** from `_system/workflows/ingest.md` with type `jira`.
