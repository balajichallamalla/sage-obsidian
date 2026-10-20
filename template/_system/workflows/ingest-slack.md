---
type: workflow
title: Ingest — Slack
---
# Workflow: ingest-slack

Targeted ingest of one Slack thread. **Mode: automatic.**

## Steps

1. Read `_system/sources/slack.md`. Follow `## Fetch one item`, then
   `python3 _system/tools/sync_state.py seen slack <channel_id>:<root_ts> --version <latest ts>`
   (exit 0 → already captured; stop). The quiet rule does not apply to targeted ingest.
2. `## Capture`, then `## Compile`.
3. `python3 _system/tools/sync_state.py mark slack <channel_id>:<root_ts> <raw path> --version <latest ts>`.
4. Run **Finish** from `_system/workflows/ingest.md` with type `slack`.
