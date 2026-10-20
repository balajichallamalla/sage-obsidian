---
type: workflow
title: Search
---
# Workflow: search (/search)

**Mode: read-only.** Quick ranked lookup — no written answer, nothing filed.

## Steps

1. Run `python3 _system/tools/search.py "<query>" -n 10` with any filters {{sage.owner.first_name}} gave:
   `--type meeting|person|project|decision|ticket|pr|concept|idea|synthesis`,
   `--since/--until YYYY-MM-DD`, `--person <slug>`, `--tag <tag>`, `--raw` (include raw captures).
2. Show the results as a short list: `[[page]]` — title (date) — first snippet line.
3. Offer: "Want an answer from these? (`/ask …`)". Change nothing in the vault.
