#!/usr/bin/env bash
# Build dist/sage-obsidian.zip for Cowork "Upload plugin". Runs the tests first.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m unittest discover -s scripts/tests >/dev/null
mkdir -p dist && rm -f dist/sage-obsidian.zip
zip -qr dist/sage-obsidian.zip .claude-plugin skills template presets scripts migrations docs README.md CHANGELOG.md LICENSE \
  -x 'scripts/dev/*' -x 'docs/specs/*' -x 'docs/plans/*' -x '*/__pycache__/*' -x '*.DS_Store'
echo "dist/sage-obsidian.zip ($(du -h dist/sage-obsidian.zip | cut -f1))"
