#!/usr/bin/env python3
"""Context for one meeting's prep brief. Pure reads; never edits files.

Usage: prep_context.py --title "<event title>" [--emails "a@x.com,Name <b@x.com>"] [--date YYYY-MM-DD] [--json]
Spec: _system/specs/2026-10-19-weekly-prep-dashboard-design.md §3.1
Env overrides (tests): VAULT_ROOT, SYNC_NOW (YYYY-MM-DD used as "today")
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from search import parse_fm, split_fm, as_list  # noqa: E402
from vault_config import owner_emails  # noqa: E402
from week_facts import BOX_RE, as_date, checkboxes, is_closed, section, today  # noqa: E402

ROOT = Path(os.environ.get("VAULT_ROOT") or Path(__file__).resolve().parents[2])
LINK_RE = re.compile(r"\[\[([^\]|#]+)")
ATTENDEE_RE = re.compile(r"^\s*(?:(.*?)\s*<([^>]+)>|(\S+@\S+))\s*$")


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


def norm_title(s):
    s = re.sub(r"\d{4}-\d{2}-\d{2}", " ", str(s))
    s = re.sub(r"\b\d{1,2}(:\d{2})?\s*(am|pm)\b|\b\d{1,2}:\d{2}\b", " ", s, flags=re.I)
    return norm(s)


def load(folder):
    out = []
    for p in sorted((ROOT / folder).glob("*.md")):
        fm_text, body = split_fm(p.read_text(encoding="utf-8", errors="replace"))
        out.append((p, parse_fm(fm_text), body))
    return out


def rel(p):
    return p.relative_to(ROOT).as_posix()


def bullets(text):
    return [l.strip()[2:].strip() for l in text.splitlines() if l.strip().startswith("- ")]


def parse_attendees(raw):
    out = []
    for item in [x for x in (raw or "").split(",") if x.strip()]:
        m = ATTENDEE_RE.match(item)
        if not m:
            out.append({"email": "", "name": item.strip()})
        elif m.group(3):
            out.append({"email": m.group(3).lower(), "name": ""})
        else:
            out.append({"email": m.group(2).strip().lower(), "name": m.group(1).strip().strip('"')})
    return [a for a in out if a["email"] not in owner_emails()]


def match_person(att, people):
    for p, fm, _ in people:
        if att["email"] and att["email"] in [e.lower() for e in as_list(fm.get("emails"))]:
            return p, fm
    local = att["email"].split("@")[0] if att["email"] else ""
    candidates = {norm(c) for c in [att["name"], local] if c}
    for p, fm, _ in people:
        names = {norm(n) for n in [fm.get("title", ""), p.stem] + as_list(fm.get("aliases"))}
        if candidates & names:
            return p, fm
    return None, None


def one_on_one(slug):
    p = ROOT / "wiki/one-on-ones" / f"1on1-{slug}.md"
    if not p.is_file():
        return None
    body = split_fm(p.read_text(encoding="utf-8"))[1]
    mine = [m.group(2).strip() for l in section(body, "My commitments").splitlines()
            if (m := BOX_RE.match(l)) and m.group(1) == " "]
    return {"path": rel(p), "open_threads": bullets(section(body, "Open threads")),
            "my_commitments_open": mine, "their_commitments": bullets(section(body, "Their commitments"))}


def context(title, emails, day):
    people = load("wiki/people")
    tickets = load("wiki/tickets")
    boxes = [b for b in checkboxes() if b["state"] == " "]
    out = {"title": title, "date": day.isoformat(), "attendees": [], "people": {}}
    link_counts = {}

    for att in parse_attendees(emails):
        p, fm = match_person(att, people)
        slug = p.stem if p else None
        out["attendees"].append({"email": att["email"], "slug": slug,
                                 "name": fm.get("title", slug) if p else (att["name"] or att["email"])})
        if not p or slug in out["people"]:
            continue
        own = {f"wiki/people/{slug}.md", f"wiki/one-on-ones/1on1-{slug}.md"}
        todos = [{"path": b["path"], "text": b["text"], "due": b["due"]} for b in boxes
                 if b["path"] in own or re.search(rf"\[\[{re.escape(slug)}(\||\]\])", b["text"])]
        tix = [{"key": tfm.get("key", tp.stem), "title": tfm.get("title", tp.stem), "status": tfm.get("status", "")}
               for tp, tfm, _ in tickets
               if f"[[{slug}]]" in str(tfm.get("assignee", "")) and not is_closed(tfm.get("status", ""))]
        out["people"][slug] = {"open_todos": todos, "one_on_one": one_on_one(slug), "tickets_in_progress": tix}
        for target in LINK_RE.findall(p.read_text(encoding="utf-8")):
            link_counts[target.strip()] = link_counts.get(target.strip(), 0) + 1

    want = norm_title(title)
    past = [(as_date(fm.get("date")), p, fm, body) for p, fm, body in load("wiki/meetings")
            if want and norm_title(fm.get("title", "")) == want and as_date(fm.get("date"))
            and as_date(fm.get("date")) < day]
    out["recurring"] = None
    if past:
        d, p, fm, body = max(past, key=lambda x: x[0])
        out["recurring"] = {"path": rel(p), "title": fm.get("title", p.stem), "date": d.isoformat(),
                            "action_items": bullets(section(body, "Action items"))}
        for target in LINK_RE.findall(body):
            link_counts[target.strip()] = link_counts.get(target.strip(), 0) + 1

    related = []
    for target, n in link_counts.items():
        stem = target.split("/")[-1]
        for folder in ("projects", "decisions"):
            q = ROOT / "wiki" / folder / f"{stem}.md"
            if q.is_file():
                fm = parse_fm(split_fm(q.read_text(encoding="utf-8"))[0])
                related.append((-n, stem, {"path": rel(q), "title": fm.get("title", stem)}))
    out["related"] = [r for _, _, r in sorted(related, key=lambda x: (x[0], x[1]))][:5]
    return out


def main(argv):
    ap = argparse.ArgumentParser(description="Context for a meeting prep brief")
    ap.add_argument("--title", required=True)
    ap.add_argument("--emails", default="")
    ap.add_argument("--date")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    day = dt.date.fromisoformat(a.date) if a.date else today()
    data = context(a.title, a.emails, day)
    if a.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"{data['title']} — {len(data['attendees'])} attendees, "
              f"last: {data['recurring']['path'] if data['recurring'] else 'none'}")
        for slug, d in data["people"].items():
            print(f"  {slug}: {len(d['open_todos'])} to-dos, {len(d['tickets_in_progress'])} tickets")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
