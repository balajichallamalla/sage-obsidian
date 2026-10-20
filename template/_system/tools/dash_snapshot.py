#!/usr/bin/env python3
"""Write, merge and report the command-center snapshot (_system/state/dashboard.json).

Usage: dash_snapshot.py write <part.json>
       dash_snapshot.py status
part.json keys (all optional): calendar, jira_worklogs | jira_hours, slack, prs,
                               errors {source: note}
Spec: _system/specs/2026-10-19-command-center-dashboard-design.md §3.1–3.2
Env overrides (tests): VAULT_ROOT, SYNC_NOW (ISO datetime, UTC)
"""
import datetime as dt
import json
import os
import sys
from pathlib import Path

ROOT = Path(os.environ.get("VAULT_ROOT") or Path(__file__).resolve().parents[2])
FILE = ROOT / "_system/state/dashboard.json"
SOURCES = ["calendar", "jira_hours", "slack", "prs"]
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
SLACK_KINDS = {"dm", "mention", "thread"}
MAX_TEXT = 140
STALE_H = 12


def now():
    raw = os.environ.get("SYNC_NOW")
    if raw:
        return dt.datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(dt.timezone.utc)
    return dt.datetime.now(dt.timezone.utc)


def fmt(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def load():
    if FILE.is_file():
        return json.loads(FILE.read_text(encoding="utf-8"))
    return {"version": 1, "generated_at": None, "sources": {}, "calendar": [],
            "jira_hours": {}, "slack": [], "prs": []}


def need(cond, msg):
    if not cond:
        raise ValueError(msg)


def check_calendar(items):
    need(isinstance(items, list), "calendar must be a list")
    for e in items:
        need(isinstance(e, dict) and e.get("start") and e.get("title"), f"calendar item needs start and title: {e}")
        e.setdefault("end", "")
        e.setdefault("attendees", 0)
        e["large"] = bool(e.get("large") or e["attendees"] > 15)
        e.setdefault("url", "")
    return sorted(items, key=lambda e: e["start"])


def check_slack(items):
    need(isinstance(items, list), "slack must be a list")
    for s in items:
        need(isinstance(s, dict) and s.get("kind") in SLACK_KINDS, f"slack kind must be one of {sorted(SLACK_KINDS)}: {s}")
        need(s.get("url"), f"slack item needs url: {s}")
        text = " ".join(str(s.get("text", "")).split())
        s["text"] = text if len(text) <= MAX_TEXT else text[:MAX_TEXT - 1] + "…"
        s.setdefault("who", "")
        s.setdefault("where", "")
        s.setdefault("ts", "")
    return items


def check_prs(items):
    need(isinstance(items, list), "prs must be a list")
    for p in items:
        need(isinstance(p, dict) and p.get("repo") and isinstance(p.get("number"), int), f"pr needs repo and int number: {p}")
        p.setdefault("title", "")
        p.setdefault("author", "")
        p.setdefault("url", "")
        p.setdefault("requested", "")
    return sorted(items, key=lambda p: p["requested"] or "9999")


def hours_from_worklogs(logs, today, target):
    need(isinstance(logs, list), "jira_worklogs must be a list")
    y, w, _ = today.isocalendar()
    by_day = {d: 0.0 for d in DAYS}
    by_ticket = {}
    for log in logs:
        if not log.get("author_is_me"):
            continue
        day = dt.date.fromisoformat(str(log["started"])[:10])
        if day.isocalendar()[:2] != (y, w):
            continue
        h = int(log["seconds"]) / 3600
        by_day[DAYS[day.weekday()]] += h
        by_ticket[log["key"]] = by_ticket.get(log["key"], 0.0) + h
    tickets = sorted(({"key": k, "hours": round(v, 2)} for k, v in by_ticket.items()), key=lambda x: (-x["hours"], x["key"]))
    return {"week": f"{y}-W{w:02d}", "target_h": target, "total_h": round(sum(by_day.values()), 2),
            "by_day": {d: round(v, 2) for d, v in by_day.items()}, "by_ticket": tickets}


def merge(data, part, t):
    stamp = fmt(t)
    errors = part.get("errors") or {}
    data.setdefault("sources", {})
    target = (data.get("jira_hours") or {}).get("target_h", 40)
    done = {}
    if "calendar" in part:
        done["calendar"] = check_calendar(part["calendar"])
    if "jira_worklogs" in part:
        done["jira_hours"] = hours_from_worklogs(part["jira_worklogs"], t.date(), target)
    elif "jira_hours" in part:
        done["jira_hours"] = part["jira_hours"]
    if "slack" in part:
        done["slack"] = check_slack(part["slack"])
    if "prs" in part:
        done["prs"] = check_prs(part["prs"])
    for src, value in done.items():
        data[src] = value
        data["sources"][src] = {"at": stamp, "ok": True, "note": "", "data_at": stamp}
    for src, note in errors.items():
        need(src in SOURCES, f"unknown source in errors: {src}")
        old = data["sources"].get(src, {})
        data["sources"][src] = {"at": stamp, "ok": False, "note": str(note), "data_at": old.get("data_at")}
    data["version"] = 1
    data["generated_at"] = stamp
    return data


def status(data, t):
    lines = []
    for src in SOURCES:
        s = data.get("sources", {}).get(src)
        if not s:
            lines.append(f"{src:<11} never")
            continue
        age = "no data"
        if s.get("data_at"):
            hrs = (t - dt.datetime.fromisoformat(s["data_at"].replace("Z", "+00:00"))).total_seconds() / 3600
            age = f"{hrs:.1f}h old" + (" (stale)" if hrs > STALE_H else "")
        lines.append(f"{src:<11} {'ok' if s.get('ok') else 'error'}  {age}  {s.get('note', '')}".rstrip())
    return "\n".join(lines)


def main(argv):
    if argv[:1] == ["write"] and len(argv) == 2:
        try:
            part = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
            data = merge(load(), part, now())
        except (ValueError, KeyError, TypeError) as e:
            print(f"invalid snapshot part: {e}", file=sys.stderr)
            return 2
        FILE.parent.mkdir(parents=True, exist_ok=True)
        FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(status(data, now()))
        return 0
    if argv == ["status"]:
        print(status(load(), now()))
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
