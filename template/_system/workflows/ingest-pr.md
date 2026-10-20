---
type: workflow
title: Ingest — PR
---
# Workflow: ingest-pr

Targeted ingest of one GitHub PR. **Mode: automatic.**

## Steps

1. Read `_system/sources/github-prs.md`. Follow `## Fetch one item`, then
   `python3 _system/tools/sync_state.py seen github-prs <repo>#<n> --version <state>`
   (exit 0 → already current; stop), then `## Compile`.
2. `python3 _system/tools/sync_state.py mark github-prs <repo>#<n> wiki/prs/<repo>-<n>.md --version <state>`.
3. Run **Finish** from `_system/workflows/ingest.md` with type `pr`.
