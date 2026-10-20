#!/usr/bin/env python3
"""Render a sage-obsidian vault from a config file and the plugin's template.

Usage:
  render_vault.py --config CONFIG.json --out VAULT [--update] [--template DIR] [--dry-run]

New vault (default): VAULT must be missing or empty.
--update: re-render framework files in an existing vault (add/remove modules, upgrades); seed
          files that already exist and everything under raw/, wiki/, journal/ are left alone.
Writes _system/.framework-manifest.json (path -> sha256 of what was rendered) so /upgrade can tell
which framework files the user has edited.
Spec: docs/specs/2026-10-20-sage-obsidian-design.md §5–6. Stdlib only.
"""
import argparse
import fnmatch
import hashlib
import json
import re
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".md", ".py", ".js", ".css", ".json", ".base", ""}
PLACEHOLDER = re.compile(r"\{\{sage\.([A-Za-z0-9_.]+)\}\}")
START = re.compile(r"^\s*(?:<!--|#|//)\s*module:(!?)([\w:-]+)\s*(?:-->)?\s*$")
END = re.compile(r"^\s*(?:<!--|#|//)\s*/module\s*(?:-->)?\s*$")
MANIFEST = "_system/.framework-manifest.json"
PROTECTED = ("raw/", "wiki/", "journal/", "_system/state/")


class RenderError(Exception):
    pass


def lookup(config, dotted):
    cur = config
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            raise KeyError(dotted)
        cur = cur[part]
    if isinstance(cur, list):
        return ", ".join(str(x) for x in cur)
    if isinstance(cur, bool):
        return "true" if cur else "false"
    return str(cur)


def module_on(config, name):
    if name == "core":
        return True
    mods = config.get("modules", {})
    if name.startswith("source:"):
        src = name.split(":", 1)[1]
        return bool(mods.get("sync")) and bool(config.get("sources", {}).get(src, {}).get("enabled"))
    return bool(mods.get(name))


def apply_blocks(text, config, where):
    out, stack = [], []
    for n, line in enumerate(text.split("\n"), 1):
        m = START.match(line)
        if m:
            stack.append(module_on(config, m.group(2)) != bool(m.group(1)))
            continue
        if END.match(line):
            if not stack:
                raise RenderError(f"{where}:{n}: /module without a module start")
            stack.pop()
            continue
        if all(stack):
            out.append(line)
    if stack:
        raise RenderError(f"{where}: module block not closed")
    return "\n".join(out)


def fill(text, config, where):
    def sub(m):
        try:
            return lookup(config, m.group(1))
        except KeyError:
            raise RenderError(f"{where}: unknown placeholder {{{{sage.{m.group(1)}}}}}")
    return PLACEHOLDER.sub(sub, text)


def owner_of(rel, modules):
    for name, patterns in modules["files"].items():
        if any(fnmatch.fnmatch(rel, p) for p in patterns):
            return name
    return "core"


def plan(config, template):
    """Return {relative path: bytes} for every file the config should produce."""
    modules = json.loads((template / "modules.json").read_text(encoding="utf-8"))
    files = {}
    for p in sorted(template.rglob("*")):
        if not p.is_file() or p.name in ("modules.json", ".DS_Store") or "__pycache__" in p.parts:
            continue
        rel = p.relative_to(template).as_posix()
        if not module_on(config, owner_of(rel, modules)):
            continue
        data = p.read_bytes()
        if p.suffix in TEXT_SUFFIXES:
            text = fill(apply_blocks(data.decode("utf-8"), config, rel), config, rel)
            data = text.encode("utf-8")
        files[rel] = data
    for d in modules.get("dirs", []):
        files.setdefault(f"{d}/.gitkeep", b"")
    return files, modules


def sha(data):
    return hashlib.sha256(data).hexdigest()


def render(config, out, template, update=False, dry_run=False):
    files, modules = plan(config, template)
    seeds = set(modules.get("seed", []))
    if out.exists() and any(out.iterdir()) and not update:
        raise RenderError(f"{out} is not empty; use --update to change an existing vault")
    if update and not (out / "_system/config.json").is_file():
        raise RenderError(f"{out} has no _system/config.json; it is not a sage-obsidian vault")
    old = {}
    if update and (out / MANIFEST).is_file():
        old = json.loads((out / MANIFEST).read_text(encoding="utf-8"))
    changes = {"written": [], "unchanged": [], "kept": [], "removed": []}
    manifest = {}
    for rel, data in files.items():
        target = out / rel
        if update and rel in seeds and target.exists():
            changes["kept"].append(rel)
            continue
        if update and rel.startswith(PROTECTED) and not rel.endswith(".gitkeep") and target.exists():
            changes["kept"].append(rel)
            continue
        if rel not in seeds:
            manifest[rel] = sha(data)
        if target.exists() and target.read_bytes() == data:
            changes["unchanged"].append(rel)
            continue
        changes["written"].append(rel)
        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    for rel in sorted(set(old) - set(manifest)):
        target = out / rel
        if target.exists() and not rel.startswith(PROTECTED):
            changes["removed"].append(rel)
            if not dry_run:
                target.unlink()
    if not dry_run:
        (out / "_system").mkdir(parents=True, exist_ok=True)
        (out / "_system/config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
        (out / MANIFEST).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return changes


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--template", default=str(PLUGIN / "template"))
    ap.add_argument("--update", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    try:
        config = json.loads(Path(a.config).read_text(encoding="utf-8"))
        changes = render(config, Path(a.out).expanduser(), Path(a.template), a.update, a.dry_run)
    except (RenderError, json.JSONDecodeError, FileNotFoundError) as e:
        print(f"render failed: {e}", file=sys.stderr)
        return 2
    for k in ("written", "removed", "kept", "unchanged"):
        print(f"{k}: {len(changes[k])}")
        if k in ("written", "removed"):
            for rel in changes[k]:
                print(f"  {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
