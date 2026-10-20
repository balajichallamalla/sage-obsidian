#!/usr/bin/env python3
"""Todoist sync helper for the second-brain vault (stdlib only).

Spec: _system/specs/2026-10-19-todoist-scheduling-search-design.md §2, §3.1
State: _system/state/sync-state.json -> sources.todoist
Env overrides (tests): VAULT_ROOT, SYNC_STATE, SYNC_NOW

Commands:
  plan --remote remote.json      print the JSON plan
  apply results.json             write 🆔/✅/❌ into the vault and update state
  status                         counts per category; open to-dos without an id
  record-project <project_id> <sections.json>
"""
import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(os.environ.get("VAULT_ROOT") or Path(__file__).resolve().parents[2])
SECTIONS = {"follow-up": "Follow-ups", "review": "Reviews", "ticket": "Tickets",
            "project": "Project work", "idea": "Ideas", "growth": "Growth"}
CONFIRM_OVER = 3
KINDS = ["create", "complete_remote", "update_remote", "delete_remote", "tick_local", "cancel_local"]
LINE_KINDS = ["create", "tick_local", "cancel_local", "complete_remote"]

LINE_RE = re.compile(r"^(?P<pre>\s*- \[)(?P<mark>[ xX-])(?P<post>\] )(?P<body>.*)$")
ID_RE = re.compile(r"\s*🆔 td:(?P<id>[A-Za-z0-9_-]+)")
DUE_RE = re.compile(r"\s*📅 (?P<due>\d{4}-\d{2}-\d{2})")
DONE_RE = re.compile(r"\s*✅ \d{4}-\d{2}-\d{2}")
CANCEL_RE = re.compile(r"\s*❌ \d{4}-\d{2}-\d{2}")
TAG_RE = re.compile(r"(?<!\S)#([A-Za-z0-9][\w/-]*)")
LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]+))?\]\]")


def sha(text):
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def now_iso():
    o = os.environ.get("SYNC_NOW")
    d = datetime.fromisoformat(o.replace("Z", "+00:00")) if o else datetime.now(timezone.utc)
    return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today():
    return now_iso()[:10]


def link_text(m):
    if m.group(2):
        return m.group(2)
    name = m.group(1).split("/")[-1]
    return name.replace("-", " ").title() if re.fullmatch(r"[a-z]+(-[a-z]+)+", name) else name


def clean(body):
    t = ID_RE.sub("", body)
    t = DONE_RE.sub("", t)
    t = CANCEL_RE.sub("", t)
    t = DUE_RE.sub("", t)
    t = LINK_RE.sub(link_text, t)
    t = TAG_RE.sub("", t)
    return re.sub(r"\s+", " ", t).strip()


def parse_line(line):
    m = LINE_RE.match(line)
    if not m:
        return None
    body = m.group("body")
    tags = TAG_RE.findall(body)
    cats = [t.split("/", 1)[1] for t in tags if t.startswith("todo/")]
    if not cats:
        return None
    idm = ID_RE.search(body)
    due = DUE_RE.search(body)
    due_s = due.group("due") if due else None
    category = cats[0] if len(cats) == 1 else None
    content = clean(body)
    return {
        "mark": "x" if m.group("mark") == "X" else m.group("mark"),
        "id": idm.group("id") if idm else None,
        "due": due_s,
        "categories": cats,
        "category": category,
        "project_tags": [t for t in tags if not t.startswith("todo/")],
        "content": content,
        "hash": sha(f"{content}|{due_s}|{category}"),
    }


def vault_files(root):
    files = sorted((root / "wiki").glob("**/*.md")) + sorted((root / "journal").glob("*.md"))
    inbox = root / "inbox.md"
    if inbox.is_file():
        files.append(inbox)
    return files


def scan(root):
    todos = []
    for f in vault_files(root):
        rel = f.relative_to(root).as_posix()
        fence = False
        for n, line in enumerate(f.read_text(encoding="utf-8").split("\n"), 1):
            if line.lstrip().startswith("```"):
                fence = not fence
                continue
            if fence:
                continue
            p = parse_line(line)
            if p:
                p.update(path=rel, line_no=n, line_hash=sha(line))
                todos.append(p)
    return todos


def state_path():
    return Path(os.environ.get("SYNC_STATE") or ROOT / "_system/state/sync-state.json")


def load_state():
    p = state_path()
    data = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    t = data.setdefault("sources", {}).setdefault("todoist", {})
    for k, v in [("project_id", None), ("sections", {}), ("cursor", None), ("seen", {}), ("last_run", None)]:
        t.setdefault(k, v)
    return data, t


def save_state(data):
    p = state_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
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


def description(t):
    path = t["path"]
    stem = path[:-3] if path.endswith(".md") else path
    lines = [f"Vault: {path}", "obsidian://open?vault=second-brain&file=" + urllib.parse.quote(stem)]
    if t["project_tags"]:
        lines.append("Project: " + " ".join("#" + p for p in t["project_tags"]))
    return "\n".join(lines)


def ref(t):
    return {"path": t["path"], "line_no": t["line_no"], "line_hash": t["line_hash"]}


def make_plan(todos, tstate, remote):
    open_r = {str(i) for i in remote.get("open", [])}
    done_r = {str(c["id"]): (c.get("completed_at") or "")[:10] for c in remote.get("completed", [])}
    seen = tstate.get("seen", {})
    plan = {k: [] for k in KINDS}
    plan["warnings"] = []
    counts = {}
    for t in todos:
        if t["id"]:
            counts[t["id"]] = counts.get(t["id"], 0) + 1
    dups = {i for i, c in counts.items() if c > 1}
    for i in sorted(dups):
        plan["warnings"].append(f"duplicate id td:{i} — not changed until resolved")
    for t in todos:
        where = f"{t['path']}:{t['line_no']}"
        if t["category"] not in SECTIONS:
            plan["warnings"].append(
                f"{where}: needs exactly one known #todo/ category (found {', '.join(t['categories'])})")
            continue
        i = t["id"]
        if i in dups:
            continue
        if not i:
            if t["mark"] == " ":
                plan["create"].append({**ref(t), "content": t["content"], "due": t["due"],
                                       "section": t["category"], "description": description(t),
                                       "hash": t["hash"]})
            continue
        s = seen.get(i)
        if t["mark"] == " ":
            if i in done_r:
                plan["tick_local"].append({**ref(t), "id": i, "date": done_r[i] or today()})
            elif i not in open_r:
                plan["cancel_local"].append({**ref(t), "id": i, "date": today()})
            elif s and s.get("hash") != t["hash"]:
                plan["update_remote"].append({"id": i, "content": t["content"], "due": t["due"],
                                              "section": t["category"], "hash": t["hash"]})
        elif t["mark"] == "x":
            if i in open_r:
                plan["complete_remote"].append({**ref(t), "id": i})
        elif t["mark"] == "-":
            if i in open_r:
                plan["delete_remote"].append({"id": i})
    for i, s in sorted(seen.items()):
        if i not in counts and s.get("status") == "open" and i in open_r:
            plan["delete_remote"].append({"id": i})
    plan["needs_confirm"] = (len(plan["cancel_local"]) > CONFIRM_OVER
                             or len(plan["delete_remote"]) > CONFIRM_OVER)
    return plan


def edit_line(line, kind, entry):
    if kind == "create":
        return line.rstrip() + f" 🆔 td:{entry['id']}"
    m = LINE_RE.match(line)
    body = m.group("body")
    if kind == "complete_remote":
        if DONE_RE.search(body):
            return line
        mark, marker = m.group("mark"), f"✅ {today()}"
    elif kind == "tick_local":
        mark, marker = "x", f"✅ {entry['date']}"
    else:  # cancel_local
        mark, marker = "-", f"❌ {entry['date']}"
    idm = ID_RE.search(body)
    if idm:
        body = body[:idm.start()].rstrip() + f" {marker}" + body[idm.start():]
    else:
        body = body.rstrip() + f" {marker}"
    return f"{m.group('pre')}{mark}{m.group('post')}{body}"


def bump_updated(lines):
    """Set frontmatter `updated:` to today (golden rule 9); no-op without frontmatter."""
    if not lines or lines[0] != "---":
        return
    for n in range(1, len(lines)):
        if lines[n] == "---":
            return
        if lines[n].startswith("updated:"):
            lines[n] = f"updated: {today()}"
            return


def apply(results, root, data, tstate):
    done = {k: 0 for k in KINDS}
    skipped, edits = [], {}
    for kind in LINE_KINDS:
        for e in results.get(kind, []):
            if kind == "create" and not e.get("id"):
                skipped.append({"kind": kind, "path": e["path"], "line_no": e["line_no"],
                                "reason": "no id returned"})
                continue
            edits.setdefault(e["path"], []).append((kind, e))
    status_after = {"tick_local": "done", "complete_remote": "done", "cancel_local": "cancelled"}
    for path, items in edits.items():
        f = root / path
        lines = f.read_text(encoding="utf-8").split("\n")
        changed = False
        for kind, e in items:
            n = e["line_no"] - 1
            if n >= len(lines) or sha(lines[n]) != e["line_hash"]:
                skipped.append({"kind": kind, "path": path, "line_no": e["line_no"],
                                "reason": "line changed since plan"})
                continue
            lines[n] = edit_line(lines[n], kind, e)
            changed = True
            done[kind] += 1
            i = str(e["id"])
            if kind == "create":
                tstate["seen"][i] = {"path": path, "hash": e["hash"], "status": "open"}
            else:
                st = tstate["seen"].setdefault(i, {"hash": None})
                st["path"] = path
                st["status"] = status_after[kind]
        if changed:
            bump_updated(lines)
            f.write_text("\n".join(lines), encoding="utf-8")
    for e in results.get("update_remote", []):
        tstate["seen"].setdefault(str(e["id"]), {"path": None, "status": "open"})["hash"] = e["hash"]
        done["update_remote"] += 1
    for e in results.get("delete_remote", []):
        tstate["seen"].setdefault(str(e["id"]), {"path": None, "hash": None})["status"] = "deleted"
        done["delete_remote"] += 1
    errors = results.get("errors", [])
    tstate["cursor"] = now_iso()
    tstate["last_run"] = {"at": now_iso(), "status": "error" if errors else "ok", **done,
                          "skipped": len(skipped), "note": "; ".join(errors)[:300]}
    save_state(data)
    return {"applied": done, "skipped": skipped}


def status(root, tstate):
    rows = {}
    for t in scan(root):
        r = rows.setdefault(t["category"] or "?", {"open": 0, "done": 0, "cancelled": 0, "no-id": 0})
        r[{" ": "open", "x": "done", "-": "cancelled"}[t["mark"]]] += 1
        if t["mark"] == " " and not t["id"]:
            r["no-id"] += 1
    lines = [f"{'category':<12} {'open':>5} {'done':>5} {'cancelled':>9} {'no-id':>6}"]
    for c in sorted(rows):
        r = rows[c]
        lines.append(f"{c:<12} {r['open']:>5} {r['done']:>5} {r['cancelled']:>9} {r['no-id']:>6}")
    lr = tstate.get("last_run")
    lines.append(f"project: {tstate.get('project_id') or 'not set'} · cursor: {tstate.get('cursor') or 'never'}")
    if lr:
        lines.append(f"last run: {lr['at']} {lr['status']} " +
                     " ".join(f"{k}={lr.get(k, 0)}" for k in KINDS) + f" skipped={lr.get('skipped', 0)}")
    return "\n".join(lines)


def main(argv):
    ap = argparse.ArgumentParser(prog="todo_sync.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan")
    p.add_argument("--remote", required=True)
    a = sub.add_parser("apply")
    a.add_argument("results")
    sub.add_parser("status")
    r = sub.add_parser("record-project")
    r.add_argument("project_id")
    r.add_argument("sections")
    args = ap.parse_args(argv)
    data, tstate = load_state()
    if args.cmd == "plan":
        remote = json.loads(Path(args.remote).read_text(encoding="utf-8"))
        print(json.dumps(make_plan(scan(ROOT), tstate, remote), indent=1, ensure_ascii=False))
    elif args.cmd == "apply":
        results = json.loads(Path(args.results).read_text(encoding="utf-8"))
        print(json.dumps(apply(results, ROOT, data, tstate), indent=1, ensure_ascii=False))
    elif args.cmd == "status":
        print(status(ROOT, tstate))
    elif args.cmd == "record-project":
        tstate["project_id"] = args.project_id
        tstate["sections"].update(json.loads(Path(args.sections).read_text(encoding="utf-8")))
        save_state(data)
        print(f"recorded project {args.project_id} with {len(tstate['sections'])} sections")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
