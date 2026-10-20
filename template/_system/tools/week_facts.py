#!/usr/bin/env python3
"""Exact facts about one ISO week of the vault, for /weekly. Pure reads; never edits files.

Usage: week_facts.py [--week 2026-W43] [--json]
Spec: _system/specs/2026-10-19-weekly-prep-dashboard-design.md §2.2 (+ my_tickets_open for "Next week")
Env overrides (tests): VAULT_ROOT, SYNC_NOW (YYYY-MM-DD used as "today")
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from search import parse_fm, split_fm, as_list  # noqa: E402
from vault_config import is_owner  # noqa: E402

ROOT = Path(os.environ.get("VAULT_ROOT") or Path(__file__).resolve().parents[2])
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
LOG_RE = re.compile(r"^## \[(\d{4}-\d{2}-\d{2})\] ([\w-]+) \| (.+)$", re.M)
BOX_RE = re.compile(r"^\s*- \[( |x|X|-)\] (.+)$")
DUE_RE = re.compile(r"📅 (\d{4}-\d{2}-\d{2})")
DONE_RE = re.compile(r"✅ (\d{4}-\d{2}-\d{2})")
DATED_BULLET_RE = re.compile(r"^\s*- (\d{4}-\d{2}-\d{2})\b")
CLOSED_WORDS = re.compile(r"\b(closed|merged|done|resolved)\b", re.I)


def today():
    return dt.date.fromisoformat(os.environ.get("SYNC_NOW", "")[:10] or dt.date.today().isoformat())


def week_range(week):
    m = re.fullmatch(r"(\d{4})-W(\d{2})", week or "")
    if not m:
        raise SystemExit(f"bad --week {week!r}; expected YYYY-Www")
    start = dt.date.fromisocalendar(int(m.group(1)), int(m.group(2)), 1)
    return start, start + dt.timedelta(days=6)


def current_week(day):
    y, w, _ = day.isocalendar()
    return f"{y}-W{w:02d}"


def as_date(s):
    m = DATE_RE.search(str(s or ""))
    return dt.date.fromisoformat(m.group(0)) if m else None


def within(s, start, end):
    d = s if isinstance(s, dt.date) else as_date(s)
    return d is not None and start <= d <= end


def pages(folder):
    base = ROOT / folder
    if not base.is_dir():
        return
    for p in sorted(base.glob("*.md")):
        fm_text, body = split_fm(p.read_text(encoding="utf-8", errors="replace"))
        yield p, parse_fm(fm_text), body


def rel(p):
    return p.relative_to(ROOT).as_posix()


def section(body, heading):
    m = re.search(rf"^## {re.escape(heading)}\s*$(.*?)(?=^## |\Z)", body, re.M | re.S)
    return m.group(1) if m else ""


def dated_bullets(text):
    for line in text.splitlines():
        m = DATED_BULLET_RE.match(line)
        if m:
            yield dt.date.fromisoformat(m.group(1)), line.strip()


def git(*args):
    r = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def git_window(start, end):
    return [f"--since={start}T00:00:00", f"--until={end}T23:59:59"]


def git_changes(start, end):
    created, updated = set(), set()
    for line in git("log", *git_window(start, end), "--name-status", "--format=").splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        path = parts[-1]
        if not (path.startswith("wiki/") and path.endswith(".md")):
            continue
        (created if parts[0] == "A" else updated).add(path)
    return created, updated - created


def git_added_boxes(start, end):
    out = set()
    diff = git("log", *git_window(start, end), "-p", "--format=", "--", "wiki", "journal", "inbox.md")
    for line in diff.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            m = BOX_RE.match(line[1:])
            if m:
                out.add(m.group(2).strip())
    return out


def todo_files():
    files = sorted((ROOT / "wiki").glob("**/*.md")) + sorted((ROOT / "journal").glob("*.md"))
    if (ROOT / "inbox.md").is_file():
        files.append(ROOT / "inbox.md")
    return files


def checkboxes():
    for p in todo_files():
        text = p.read_text(encoding="utf-8", errors="replace")
        fm = parse_fm(split_fm(text)[0])
        page_date = as_date(fm.get("created") or fm.get("date") or p.stem)
        fence = False
        for line in text.splitlines():
            if line.lstrip().startswith("```"):
                fence = not fence
                continue
            m = BOX_RE.match(line)
            if fence or not m or "#todo/" not in line:
                continue
            due, done = DUE_RE.search(line), DONE_RE.search(line)
            yield {"path": rel(p), "state": m.group(1).lower(), "text": m.group(2).strip(),
                   "due": due.group(1) if due else None, "done": done.group(1) if done else None,
                   "page_date": page_date}


def is_closed(status):
    return str(status).strip().lower().startswith(("closed", "done"))


def link(p):
    return f"[[{p.stem}]]"


def facts(week, now):
    start, end = week_range(week)
    out = {"week": week, "start": start.isoformat(), "end": end.isoformat()}

    log = (ROOT / "log.md").read_text(encoding="utf-8") if (ROOT / "log.md").is_file() else ""
    out["log"] = [{"date": d, "op": op, "title": t} for d, op, t in LOG_RE.findall(log)
                  if within(d, start, end)]

    g_created, g_updated = git_changes(start, end)
    created, updated = set(g_created), set(g_updated)
    for p in sorted((ROOT / "wiki").glob("**/*.md")):
        fm = parse_fm(split_fm(p.read_text(encoding="utf-8", errors="replace"))[0])
        if within(fm.get("created"), start, end):
            created.add(rel(p))
        elif within(fm.get("updated"), start, end):
            updated.add(rel(p))
    out["pages_created"] = sorted(created)
    out["pages_updated"] = sorted(updated - created)

    out["meetings"] = [{"path": rel(p), "title": fm.get("title", p.stem), "date": fm.get("date"),
                        "attendees": as_list(fm.get("attendees"))}
                       for p, fm, _ in pages("wiki/meetings") if within(fm.get("date"), start, end)]
    out["decisions"] = [{"path": rel(p), "title": fm.get("title", p.stem), "date": fm.get("date")}
                        for p, fm, _ in pages("wiki/decisions") if within(fm.get("date"), start, end)]

    closed, blocked, mine = [], [], []
    for p, fm, body in pages("wiki/tickets"):
        status = fm.get("status", "")
        if is_owner(fm.get("assignee", "")) and not is_closed(status):
            mine.append({"path": rel(p), "key": fm.get("key", p.stem), "title": fm.get("title", p.stem),
                         "status": status})
        if str(status).strip().lower().startswith("blocked"):
            blocked.append({"path": rel(p), "key": fm.get("key", p.stem), "title": fm.get("title", p.stem),
                            "assignee": fm.get("assignee", "")})
        if not is_closed(status):
            continue
        dates = [d for d, line in dated_bullets(body) if CLOSED_WORDS.search(line)]
        when = max(dates) if dates else as_date(fm.get("updated"))
        if within(when, start, end):
            closed.append({"path": rel(p), "key": fm.get("key", p.stem), "title": fm.get("title", p.stem),
                           "assignee": fm.get("assignee", ""), "closed": when.isoformat()})
    out["tickets_closed"], out["blocked"], out["my_tickets_open"] = closed, blocked, mine

    prs = []
    for p, fm, body in pages("wiki/prs"):
        if str(fm.get("status", "")).strip().lower() != "merged":
            continue
        dates = [as_date(m) for line in body.splitlines() if "merged" in line.lower()
                 for m in DATE_RE.findall(line)]
        when = max(dates) if dates else as_date(fm.get("updated"))
        if within(when, start, end):
            prs.append({"path": rel(p), "title": fm.get("title", p.stem), "author": fm.get("author", ""),
                        "merged": when.isoformat()})
    out["prs_merged"] = prs

    added_git = git_added_boxes(start, end)
    boxes = list(checkboxes())
    cutoff = min(now, end + dt.timedelta(days=1))
    nxt = (end + dt.timedelta(days=1), end + dt.timedelta(days=7))
    slim = lambda b: {"path": b["path"], "text": b["text"], "due": b["due"]}
    out["todos_done"] = [slim(b) for b in boxes if b["state"] == "x" and within(b["done"], start, end)]
    out["todos_added"] = [slim(b) for b in boxes
                          if within(b["page_date"], start, end) or b["text"] in added_git]
    out["todos_overdue"] = [slim(b) for b in boxes
                            if b["state"] == " " and b["due"] and as_date(b["due"]) < cutoff]
    out["todos_next_week"] = [slim(b) for b in boxes if b["state"] == " " and within(b["due"], *nxt)]

    active = []
    for p, fm, body in pages("wiki/projects"):
        bullets = [(d, line) for d, line in dated_bullets(section(body, "Timeline")) if start <= d <= end]
        if bullets:
            active.append({"path": rel(p), "title": fm.get("title", p.stem), "tags": as_list(fm.get("tags")),
                           "last": max(d for d, _ in bullets).isoformat(), "bullets": [l for _, l in bullets]})
    out["projects_active"] = active

    digests = []
    for p in sorted((ROOT / "_system/state/digests").glob("*.md")):
        if re.search(r"^status: pending\s*$", p.read_text(encoding="utf-8"), re.M):
            digests.append(rel(p))
    out["digests_pending"] = digests

    wins = []
    for pr in prs:
        if is_owner(pr["author"]):
            wins.append({"kind": "pr", "link": link(Path(pr["path"])), "title": pr["title"], "date": pr["merged"]})
    for t in closed:
        if is_owner(t["assignee"]):
            wins.append({"kind": "ticket", "link": link(Path(t["path"])), "title": t["title"], "date": t["closed"]})
    for a in active:
        if "automation" in a["tags"]:
            wins.append({"kind": "automation", "link": link(Path(a["path"])), "title": a["title"], "date": a["last"]})
    out["wins"] = wins
    return out


def main(argv):
    ap = argparse.ArgumentParser(description="Facts about one ISO week of the vault")
    ap.add_argument("--week")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    now = today()
    data = facts(a.week or current_week(now), now)
    if a.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"{data['week']} ({data['start']} → {data['end']})")
        for k, v in data.items():
            if isinstance(v, list):
                print(f"  {k}: {len(v)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
