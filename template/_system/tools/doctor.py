#!/usr/bin/env python3
"""File-level health checks for a sage-obsidian vault (read-only).

Usage: python3 _system/tools/doctor.py [--json]
Prints one line per check: "ok|warn|fail  <name>  <detail>  [→ fix]". Exit 1 if any check fails.
Connector reachability and scheduled tasks are checked by the doctor skill itself (they need Claude's
tools); this script covers everything visible on disk.
Env override (tests): VAULT_ROOT
"""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vault_config import load, root  # noqa: E402

SCHEMA_VERSION = 1


def run(*args):
    r = subprocess.run(list(args), cwd=root(), capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def checks():
    R = root()
    cfg = load()
    out = []
    add = lambda status, name, detail, fix="": out.append({"status": status, "name": name, "detail": detail, "fix": fix})
    if not cfg:
        add("fail", "config", "_system/config.json missing or invalid", "run sage-obsidian setup in this folder")
        return out
    v = cfg.get("schema_version")
    add("ok" if v == SCHEMA_VERSION else "fail", "config", f"schema v{v}, plugin {cfg.get('plugin_version', '?')}",
        "" if v == SCHEMA_VERSION else "run sage-obsidian upgrade")
    on = [k for k, val in cfg.get("modules", {}).items() if val]
    add("ok", "modules", ", ".join(["core"] + on))
    manifest = R / "_system/.framework-manifest.json"
    if manifest.is_file():
        missing = [p for p in json.loads(manifest.read_text()) if not (R / p).exists()]
        add("fail" if missing else "ok", "framework files",
            f"{len(missing)} missing: {', '.join(missing[:3])}" if missing else "all present",
            "run sage-obsidian setup (change mode) to restore them" if missing else "")
    else:
        add("warn", "framework files", "no .framework-manifest.json", "run sage-obsidian setup (change mode)")
    plugins = R / ".obsidian/community-plugins.json"
    enabled = json.loads(plugins.read_text()) if plugins.is_file() else []
    installed = {p.name for p in (R / ".obsidian/plugins").glob("*") if (p / "main.js").is_file()}
    for pid, label in [("dataview", "Dataview"), ("obsidian-tasks-plugin", "Tasks")]:
        if pid in installed and pid in enabled:
            add("ok", label, "installed and enabled")
        else:
            add("warn", label, "not installed" if pid not in installed else "installed but not enabled",
                f"Obsidian → Settings → Community plugins → install and enable {label}")
    dv = R / ".obsidian/plugins/dataview/data.json"
    dv_cfg = json.loads(dv.read_text()) if dv.is_file() else {}
    if cfg.get("modules", {}).get("dashboard"):
        add("ok" if dv_cfg.get("enableDataviewJs") else "fail", "Dataview JS queries",
            "on" if dv_cfg.get("enableDataviewJs") else "off",
            "" if dv_cfg.get("enableDataviewJs") else "Settings → Dataview → Enable JavaScript queries")
    code, text = run(sys.executable, "_system/tests/check_vault.py")
    add("ok" if code == 0 else "fail", "validator", text.splitlines()[-1] if text else "no output",
        "" if code == 0 else "run python3 _system/tests/check_vault.py and fix the FAIL lines")
    code, text = run("git", "status", "--porcelain")
    if code != 0:
        add("fail", "git", "not a git repository", "run: git init && git add -A && git commit -m 'setup'")
    else:
        n = len([l for l in text.splitlines() if l.strip()])
        add("ok" if n == 0 else "warn", "git", "clean" if n == 0 else f"{n} uncommitted changes",
            "" if n == 0 else "review with git status, then commit")
        code, remotes = run("git", "remote")
        add("ok" if not remotes else "fail", "git remote", "none (local only)" if not remotes else remotes,
            "" if not remotes else "remove it: git remote remove <name> (this vault must stay local)")
    lock = R / "_system/state/run.lock"
    if lock.is_file():
        try:
            started = datetime.fromisoformat(json.loads(lock.read_text())["started"].replace("Z", "+00:00"))
            hours = (datetime.now(timezone.utc) - started).total_seconds() / 3600
        except (ValueError, KeyError, json.JSONDecodeError):
            hours = 99
        add("warn" if hours > 2 else "ok", "run lock", f"held {hours:.1f}h",
            "python3 _system/tools/run_lock.py release" if hours > 2 else "")
    else:
        add("ok", "run lock", "free")
    pending = [p.name for p in (R / "_system/state/digests").glob("*.md") if "status: pending" in p.read_text()]
    add("warn" if pending else "ok", "digests", f"{len(pending)} pending" if pending else "none pending",
        "reply ok to the pending sync digest" if pending else "")
    return out


def main(argv):
    results = checks()
    if "--json" in argv:
        print(json.dumps(results, indent=2))
    else:
        for r in results:
            fix = f"  → {r['fix']}" if r["fix"] else ""
            print(f"{r['status']:<5} {r['name']:<20} {r['detail']}{fix}")
    return 1 if any(r["status"] == "fail" for r in results) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
