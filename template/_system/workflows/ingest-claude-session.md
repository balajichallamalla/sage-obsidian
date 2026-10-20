---
type: workflow
title: Ingest — Claude session
---
# Workflow: ingest-claude-session

Targeted ingest of one Claude session. **Mode: automatic.**

## Steps

1. Read `_system/sources/claude-sessions.md`. Follow `## Fetch one item`, then
   `python3 _system/tools/sync_state.py seen claude-sessions <id> --version <last ts>`
   (exit 0 → already captured; stop), then `## Capture` and `## Compile`.
2. `python3 _system/tools/sync_state.py mark claude-sessions <id> <raw path> --version <last ts>`.
3. Run **Finish** from `_system/workflows/ingest.md` with type `claude-session`.
