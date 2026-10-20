---
type: workflow
title: Ingest — email
---
# Workflow: ingest-email

Targeted ingest of one Gmail thread. **Mode: Discuss first.**

## Steps

1. Read `_system/sources/gmail.md`. Follow `## Fetch one item`, apply the sensitive screen
   (if it matches, tell {{sage.owner.first_name}} and stop), then
   `python3 _system/tools/sync_state.py seen gmail <threadId> --version <newest date>`
   (exit 0 → already filed; stop), then `## Capture`.
2. Discuss first: show takeaways, asks, proposed to-dos, pages to touch; wait for the user's reply.
3. `## Compile` with {{sage.owner.first_name}}'s corrections.
4. `python3 _system/tools/sync_state.py mark gmail <threadId> <raw path> --version <newest date>`.
5. Run **Finish** from `_system/workflows/ingest.md` with type `email`.
