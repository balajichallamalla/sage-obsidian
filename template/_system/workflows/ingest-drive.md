---
type: workflow
title: Ingest — Drive meeting notes
---
# Workflow: ingest-drive

Targeted ingest of one Google Drive doc (Gemini meeting notes). **Mode: Discuss first.**

## Steps

1. Read `_system/sources/drive-meetings.md`. Follow `## Fetch one item`, `## Dedupe key`
   (`python3 _system/tools/sync_state.py seen drive-meetings <fileId> --version <modifiedTime>`;
   exit 0 → tell {{sage.owner.first_name}} it is already filed and stop), then `## Capture`.
2. Continue with `_system/workflows/ingest-meeting.md` from step 2 (orient → discuss first →
   write pages).
3. `python3 _system/tools/sync_state.py mark drive-meetings <fileId> <wiki meeting path> --version <modifiedTime>`.
4. Run **Finish** from `_system/workflows/ingest.md` with type `meeting`.
