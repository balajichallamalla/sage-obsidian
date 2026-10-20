---
type: workflow
title: Sync status
---
# Workflow: sync-status (/sync-status)

Read-only.

## Steps

1. Run `python3 _system/tools/sync_state.py status` and show the table.
2. List `_system/state/digests/*.md` with `status: pending` (path + window).
3. List sources in `_system/sources/` vs the six expected; name any not built yet.
4. Say what to run next: a pending digest to apply, `/sync`, or `/sync --backfill` if any
   source shows backfill not done.
