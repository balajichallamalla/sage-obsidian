#!/usr/bin/env bash
# Copy the framework (never content) from a working vault into template/, then generalize it.
# Usage: scripts/dev/import_vault.sh ~/Desktop/second-brain
set -euo pipefail
V="${1:?vault path}"; T="$(cd "$(dirname "$0")/../.." && pwd)/template"
keep=(modules.json CLAUDE.md _system/tests/check_vault.py _system/tools/vault_config.py
      _system/tools/doctor.py _system/tests/test_vault_config.py _system/tests/test_doctor.py index.md log.md inbox.md
      _system/normalize.md)
stash="$(mktemp -d)"; for f in "${keep[@]}"; do [ -e "$T/$f" ] && mkdir -p "$stash/$(dirname "$f")" && cp "$T/$f" "$stash/$f"; done
rm -rf "$T"; mkdir -p "$T"
for f in todos.md home.md .gitignore _system/HELP.md _system/SETUP.md .obsidian/app.json .obsidian/appearance.json .obsidian/core-plugins.json \
         .obsidian/community-plugins.json .obsidian/daily-notes.json .obsidian/graph.json .obsidian/templates.json \
         .obsidian/plugins/dataview/data.json; do mkdir -p "$T/$(dirname "$f")"; cp "$V/$f" "$T/$f"; done
for d in workflows page-types templates sources tools tests dashboard; do mkdir -p "$T/_system/$d"; cp -R "$V/_system/$d/." "$T/_system/$d/"; done
find "$T" -name __pycache__ -prune -exec rm -rf {} + ; find "$T" -name .DS_Store -delete
python3 "$(dirname "$0")/generalize_template.py" "$T"
cp -R "$stash/." "$T/"; rm -rf "$stash"
echo "template imported from $V (hand-written files kept: ${keep[*]})"
