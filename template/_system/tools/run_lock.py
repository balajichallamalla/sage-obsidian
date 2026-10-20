#!/usr/bin/env python3
"""Run lock for scheduled and manual vault runs (stdlib only).

File: _system/state/run.lock (git-ignored). Env overrides: RUN_LOCK (path), SYNC_NOW (clock).
Spec: _system/specs/2026-10-19-todoist-scheduling-search-design.md §3.4

Commands:
  acquire --owner NAME [--stale-hours 2]   exit 0 acquired, 3 held by a fresh lock
  release                                  remove the lock (no-op if absent)
  status                                   print "free" or "held by NAME since TIME"
"""
import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def lock_path():
    return Path(os.environ.get("RUN_LOCK") or ROOT / "_system/state/run.lock")


def now():
    o = os.environ.get("SYNC_NOW")
    d = datetime.fromisoformat(o.replace("Z", "+00:00")) if o else datetime.now(timezone.utc)
    return d.astimezone(timezone.utc).replace(microsecond=0)


def fmt(d):
    return d.strftime("%Y-%m-%dT%H:%M:%SZ")


def read_lock():
    p = lock_path()
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"owner": "unknown", "started": "1970-01-01T00:00:00Z"}


def main(argv):
    ap = argparse.ArgumentParser(prog="run_lock.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("acquire")
    a.add_argument("--owner", required=True)
    a.add_argument("--stale-hours", type=float, default=2.0)
    sub.add_parser("release")
    sub.add_parser("status")
    args = ap.parse_args(argv)
    cur = read_lock()
    if args.cmd == "status":
        print("free" if not cur else f"held by {cur['owner']} since {cur['started']}")
        return 0
    if args.cmd == "release":
        if lock_path().exists():
            lock_path().unlink()
        return 0
    note = "acquired"
    if cur:
        started = datetime.fromisoformat(cur["started"].replace("Z", "+00:00"))
        if now() - started < timedelta(hours=args.stale_hours):
            print(f"held by {cur['owner']} since {cur['started']}")
            return 3
        note = f"acquired (replaced stale lock held by {cur['owner']} since {cur['started']})"
    lock_path().parent.mkdir(parents=True, exist_ok=True)
    lock_path().write_text(json.dumps({"owner": args.owner, "started": fmt(now())}), encoding="utf-8")
    print(note)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
