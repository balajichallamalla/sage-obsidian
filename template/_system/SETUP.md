---
type: setup
title: One-time setup
---
# One-time setup (manual)

Claude can't install Obsidian plugins for you. Do these once:

1. **Settings → Community plugins → Turn on**, then browse and install + enable:
   - [ ] **Dataview** — powers the `home.md` command center. The vault ships its settings
     (JavaScript queries on, task completion writes `✅ date`); after enabling, toggle the plugin
     off and on once so it reads them. Check: Settings → Dataview → **Enable JavaScript queries** is on.
   - [ ] **Tasks** — powers `todos.md` and journal overdue lists
   - [ ] **Templater** — optional; core Templates already work with `_system/templates/`
   - [ ] **Obsidian Git** — optional auto-commit (leave *push* disabled — local only)
2. **Browser:** install **Obsidian Web Clipper**; set its default folder to `raw/clips`.
3. **Hotkey:** Settings → Hotkeys → "Download attachments for current file" → e.g. `Ctrl+Shift+D`
   (saves clipped images into `raw/assets/`).
4. **Do not enable Obsidian Sync or iCloud for this vault** — it holds company-confidential notes.
5. Verify: open `todos.md` — you should see empty query sections, not code blocks.
