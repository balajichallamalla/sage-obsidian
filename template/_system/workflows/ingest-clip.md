---
type: workflow
title: Ingest — clip
---
# Workflow: ingest-clip

**Mode: automatic.** For articles and docs saved to `raw/clips/` (e.g. by Obsidian Web Clipper).

## Steps

1. Read the clip. If it references images in `raw/assets/`, read the text first, then view the
   images that matter.
2. Read `index.md` for related concepts, projects, repos.
3. Create or update `wiki/concepts/<slug>.md` for each core concept (max 3 new pages per clip).
   If the clip mainly answers a question or compares options, create a
   `wiki/syntheses/<slug>.md` instead.
4. Add a line to `## How it applies here` on related project/repo pages if relevant.
5. `sources:` on every touched page includes the clip path.
6. Run **Finish** from `_system/workflows/ingest.md` with type `clip`.
