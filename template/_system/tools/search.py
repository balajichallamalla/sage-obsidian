#!/usr/bin/env python3
"""Ranked keyword search over the second-brain vault (stdlib BM25).

Usage: search.py "<query>" [--type T] [--since D] [--until D] [--person SLUG] [--tag T]
                 [--raw] [-n 10] [--json]
Spec: _system/specs/2026-10-19-todoist-scheduling-search-design.md §3.5
Env override (tests): VAULT_ROOT
"""
import argparse
import json
import math
import os
import re
import sys
from pathlib import Path

ROOT = Path(os.environ.get("VAULT_ROOT") or Path(__file__).resolve().parents[2])
TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_-]*")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
K1, B = 1.5, 0.5
LINK_RE = re.compile(r"\[\[([^\]|#]+)")


def tokens(text):
    return TOKEN_RE.findall(text.lower())


def split_fm(text):
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end != -1:
            return text[4:end], text[end + 4:].lstrip("\n")
    return "", text


def parse_fm(fm):
    out = {}
    for line in fm.splitlines():
        m = re.match(r"^([A-Za-z][\w-]*):\s*(.*)$", line)
        if not m:
            continue
        v = m.group(2).strip()
        if v.startswith("[") and v.endswith("]"):
            v = [x.strip().strip('"').strip("'") for x in v[1:-1].split(",") if x.strip()]
        else:
            v = v.strip('"').strip("'")
        out[m.group(1)] = v
    return out


def as_list(v):
    return v if isinstance(v, list) else ([v] if v else [])


def load_docs(root, include_raw):
    docs = []
    groups = [("wiki", 1.0)] + ([("raw", 0.6)] if include_raw else [])
    for folder, weight in groups:
        for p in sorted((root / folder).glob("**/*.md")):
            text = p.read_text(encoding="utf-8", errors="replace")
            fm_text, body = split_fm(text)
            fm = parse_fm(fm_text)
            title = fm.get("title") or p.stem
            aliases = as_list(fm.get("aliases"))
            headings = " ".join(l.lstrip("#") for l in body.splitlines() if l.startswith("#"))
            tf = {}
            for tok in tokens(" ".join([title, p.stem] + aliases)):
                tf[tok] = tf.get(tok, 0) + 3
            for tok in tokens(headings):
                tf[tok] = tf.get(tok, 0) + 2
            for tok in tokens(body):
                tf[tok] = tf.get(tok, 0) + 1
            date = str(fm.get("date") or "")
            if not DATE_RE.fullmatch(date):
                m = DATE_RE.match(p.name)
                date = m.group(0) if m else str(fm.get("created") or "")
            docs.append({"path": p.relative_to(root).as_posix(), "slug": p.stem, "title": title,
                         "aliases": aliases, "type": fm.get("type", ""), "date": date,
                         "tags": as_list(fm.get("tags")), "fm_text": fm_text, "body": body,
                         "tf": tf, "len": sum(tf.values()) or 1, "weight": weight})
    inbound = {}
    for d in docs:
        for target in set(LINK_RE.findall(d["fm_text"] + "\n" + d["body"])):
            slug = target.strip().split("/")[-1]
            if slug != d["slug"]:
                inbound[slug] = inbound.get(slug, 0) + 1
    for d in docs:
        d["authority"] = 1 + 0.25 * math.log(1 + inbound.get(d["slug"], 0))
    return docs


def load_normalize(root):
    pairs, in_table = [], False
    p = root / "_system/normalize.md"
    if not p.is_file():
        return pairs
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip().startswith("|"):
            in_table = False
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(set(c) <= set("-: ") for c in cells):
            in_table = True
            continue
        if in_table and len(cells) >= 2 and cells[0]:
            pairs.append((cells[0], cells[1]))
    return pairs


def phrase_in(phrase, q):
    return bool(phrase) and re.search(r"(?<![a-z0-9])" + re.escape(phrase.lower()) + r"(?![a-z0-9])", q)


def expand(query, docs, pairs):
    q = query.lower()
    extra = [right for wrong, right in pairs if phrase_in(wrong, q)]
    for d in docs:
        if any(phrase_in(a, q) for a in d["aliases"] + [d["title"]]):
            extra.append(d["slug"])
    return list(dict.fromkeys(tokens(query + " " + " ".join(extra))))


def keep(d, a):
    if a.type and d["type"] != a.type:
        return False
    if a.since and (not d["date"] or d["date"] < a.since):
        return False
    if a.until and (not d["date"] or d["date"] > a.until):
        return False
    if a.person and d["slug"] != a.person and f"[[{a.person}" not in d["fm_text"] + d["body"]:
        return False
    if a.tag and a.tag not in d["tags"] and f"#{a.tag}" not in d["body"]:
        return False
    return True


def rank(docs, qtoks):
    n = len(docs)
    if not n:
        return []
    avg = sum(d["len"] for d in docs) / n
    df = {t: sum(1 for d in docs if t in d["tf"]) for t in qtoks}
    out = []
    for d in docs:
        s = 0.0
        for t in qtoks:
            f = d["tf"].get(t)
            if not f:
                continue
            idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
            s += idf * f * (K1 + 1) / (f + K1 * (1 - B + B * d["len"] / avg))
        if s > 0:
            out.append((round(s * d["weight"] * d["authority"], 3), d))
    out.sort(key=lambda x: (-x[0], x[1]["path"]))
    return out


def snippet(d, qtoks):
    qs, out = set(qtoks), []
    for line in d["body"].splitlines():
        if line.strip() and not line.startswith("#") and qs & set(tokens(line)):
            out.append(line.strip()[:160])
            if len(out) == 2:
                break
    return out


def main(argv):
    ap = argparse.ArgumentParser(prog="search.py")
    ap.add_argument("query")
    ap.add_argument("--type")
    ap.add_argument("--since")
    ap.add_argument("--until")
    ap.add_argument("--person")
    ap.add_argument("--tag")
    ap.add_argument("--raw", action="store_true")
    ap.add_argument("-n", type=int, default=10)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    all_docs = load_docs(ROOT, a.raw)
    qtoks = expand(a.query, all_docs, load_normalize(ROOT))
    hits = rank([d for d in all_docs if keep(d, a)], qtoks)[: a.n]
    results = [{"rank": i + 1, "path": d["path"], "title": d["title"], "date": d["date"],
                "score": s, "snippet": snippet(d, qtoks)} for i, (s, d) in enumerate(hits)]
    if a.json:
        print(json.dumps(results, indent=1, ensure_ascii=False))
    else:
        for r in results:
            print(f"{r['rank']}. {r['path']} — {r['title']} ({r['date'] or 'no date'}) [{r['score']}]")
            for s in r["snippet"]:
                print(f"   {s}")
        if not results:
            print("no matches")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
