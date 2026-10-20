#!/usr/bin/env python3
"""Sync state helper for the second-brain vault (stdlib only).

State file: _system/state/sync-state.json (tests override with SYNC_STATE; "now" with SYNC_NOW).
Spec: _system/specs/2026-10-18-connector-ingestion-design.md §2.3

Commands:
  window <source> [--backfill]      print "START END" or "DONE"
  seen <source> <id> [--version V]  exit 0 seen, 1 new, 2 seen-but-changed
  mark <source> <id> <path> [--version V]
  advance <source> <iso> [--backfill]
  run <source> --status ok|error --fetched N --new N --updated N [--note TEXT]
  split <start> <end>
  status
"""
import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ["drive-meetings", "jira", "slack", "gmail", "github-prs", "claude-sessions"]
BACKFILL_START = "{{sage.sync.backfill_start}}T00:00:00Z"
WEEK = timedelta(days=7)


def parse(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


def fmt(d):
    return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def now():
    o = os.environ.get("SYNC_NOW")
    return parse(o) if o else datetime.now(timezone.utc).replace(microsecond=0)


def state_path():
    return Path(os.environ.get("SYNC_STATE", ROOT / "_system/state/sync-state.json"))


def load():
    p = state_path()
    data = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    data.setdefault("backfill_start", BACKFILL_START)
    srcs = data.setdefault("sources", {})
    for s in SOURCES:
        e = srcs.setdefault(s, {})
        for k, v in [("cursor", None), ("backfill_pos", None), ("backfill_end", None),
                     ("backfill_done", False), ("seen", {}), ("last_run", None)]:
            e.setdefault(k, v)
    return data


def save(data):
    p = state_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, indent=2, sort_keys=True) + "\n"
    fd, tmp = tempfile.mkstemp(dir=p.parent, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    try:
        os.replace(tmp, p)
    except OSError:  # some mounted folders refuse rename; fall back to direct write
        p.write_text(text, encoding="utf-8")
        try:
            os.unlink(tmp)
        except OSError:
            pass


class UsageError(Exception):
    pass


def source(data, name):
    if name not in SOURCES:
        raise UsageError(f"unknown source: {name} (expected one of {', '.join(SOURCES)})")
    return data["sources"][name]


def ensure_backfill_end(s, n):
    if s["backfill_end"] is None:
        start = s["cursor"] or fmt(n - WEEK)
        s["backfill_end"] = start
        if s["cursor"] is None:
            s["cursor"] = start


def cmd_window(a, data):
    s, n = source(data, a.source), now()
    ensure_backfill_end(s, n)
    if a.backfill:
        pos = parse(s["backfill_pos"] or data["backfill_start"])
        end = parse(s["backfill_end"])
        if pos >= end:
            s["backfill_done"] = True
            save(data)
            print("DONE")
            return 0
        save(data)
        print(fmt(pos), fmt(min(pos + WEEK, end)))
        return 0
    save(data)
    print(s["cursor"], fmt(n))
    return 0


def cmd_seen(a, data):
    e = source(data, a.source)["seen"].get(a.id)
    if e is None:
        return 1
    if a.version is not None and e.get("version") != a.version:
        return 2
    return 0


def cmd_mark(a, data):
    source(data, a.source)["seen"][a.id] = {"path": a.path, "version": a.version}
    save(data)
    return 0


def cmd_advance(a, data):
    s, t = source(data, a.source), parse(a.iso)
    if a.backfill:
        s["backfill_pos"] = fmt(t)
        if s["backfill_end"] and t >= parse(s["backfill_end"]):
            s["backfill_done"] = True
    elif s["cursor"] is None or t > parse(s["cursor"]):
        s["cursor"] = fmt(t)
    save(data)
    return 0


def cmd_run(a, data):
    source(data, a.source)["last_run"] = {
        "at": fmt(now()), "status": a.status, "fetched": a.fetched,
        "new": a.new, "updated": a.updated, "note": a.note or ""}
    save(data)
    return 0


def cmd_split(a, data):
    s, e = parse(a.start), parse(a.end)
    if e <= s:
        raise UsageError("end must be after start")
    mid = s + (e - s) / 2
    print(fmt(s), fmt(mid))
    print(fmt(mid), fmt(e))
    return 0


def cmd_status(a, data):
    print(f"{'source':<16} {'cursor':<21} {'backfill':<24} {'last run'}")
    for name in SOURCES:
        s = data["sources"][name]
        bf = "done" if s["backfill_done"] else (f"at {s['backfill_pos'][:10]}" if s["backfill_pos"] else "not started")
        lr = s["last_run"]
        last = f"{lr['at']} {lr['status']} new={lr['new']} upd={lr['updated']} {lr['note']}".strip() if lr else "never"
        print(f"{name:<16} {s['cursor'] or '-':<21} {bf:<24} {last}  seen={len(s['seen'])}")
    return 0


def build_parser():
    p = argparse.ArgumentParser(prog="sync_state.py")
    sub = p.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("window"); w.add_argument("source"); w.add_argument("--backfill", action="store_true")
    s = sub.add_parser("seen"); s.add_argument("source"); s.add_argument("id"); s.add_argument("--version")
    m = sub.add_parser("mark"); m.add_argument("source"); m.add_argument("id"); m.add_argument("path"); m.add_argument("--version")
    ad = sub.add_parser("advance"); ad.add_argument("source"); ad.add_argument("iso"); ad.add_argument("--backfill", action="store_true")
    r = sub.add_parser("run"); r.add_argument("source")
    r.add_argument("--status", choices=["ok", "error"], required=True)
    for f in ["--fetched", "--new", "--updated"]:
        r.add_argument(f, type=int, required=True)
    r.add_argument("--note")
    sp = sub.add_parser("split"); sp.add_argument("start"); sp.add_argument("end")
    sub.add_parser("status")
    return p


COMMANDS = {"window": cmd_window, "seen": cmd_seen, "mark": cmd_mark, "advance": cmd_advance,
            "run": cmd_run, "split": cmd_split, "status": cmd_status}


def main(argv):
    parser = build_parser()
    try:
        a = parser.parse_args(argv)
    except SystemExit as e:
        return 3 if e.code else 0
    try:
        return COMMANDS[a.cmd](a, load())
    except (UsageError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
