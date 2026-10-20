# Customizing your vault

- **Rules** — `CLAUDE.md`. Claude reads it before every command. Keep it under 130 lines.
- **Procedures** — `_system/workflows/<command>.md`. Change steps, add a recipe, or write a new
  workflow and a routing row in `CLAUDE.md`.
- **Page shapes** — edit the `TYPES` table in `_system/tools/gen_page_types.py` and run it; it rewrites
  `_system/page-types/` and `_system/templates/`.
- **A new source** — copy a file in `_system/sources/` and keep its sections (Fetch window, Fetch one
  item, Filter, Dedupe key, Capture, Compile, Mode).
- **Name fixes** — add rows to `_system/normalize.md` (e.g. "Core Logix" → "Coralogix").
- **Dashboard** — `_system/dashboard/command-center/view.js` and `view.css`.
- **Settings** — `_system/config.json`; re-run setup to apply module/source changes safely.

After editing, run `python3 _system/tests/check_vault.py`. `upgrade` keeps your edits: it shows a diff
and asks before replacing a file you changed.
