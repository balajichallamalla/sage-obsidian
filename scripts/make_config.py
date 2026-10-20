#!/usr/bin/env python3
"""Build a full config.json from presets/_base.json + a role preset + the setup answers.

Usage: make_config.py --preset engineer --answers answers.json [--out config.json]
answers.json holds only what the interview collected (owner, vault, modules, sources, ...);
anything missing falls back to the preset, then to _base.json. Prints the config if --out is omitted.
"""
import argparse
import copy
import datetime as dt
import json
import sys
from pathlib import Path

PRESETS = Path(__file__).resolve().parents[1] / "presets"


def merge(base, over):
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        out[k] = merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else copy.deepcopy(v)
    return out


def build(preset, answers, today=None):
    base = json.loads((PRESETS / "_base.json").read_text(encoding="utf-8"))
    p = json.loads((PRESETS / f"{preset}.json").read_text(encoding="utf-8"))
    p = {k: v for k, v in p.items() if k not in ("label", "description")}
    cfg = merge(merge(base, p), answers)
    today = today or dt.date.today()
    cfg["preset"] = preset
    cfg["setup_date"] = cfg.get("setup_date") or today.isoformat()
    if not cfg["sync"].get("backfill_start"):
        cfg["sync"]["backfill_start"] = (today - dt.timedelta(weeks=8)).isoformat()
    o = cfg["owner"]
    if not o.get("first_name") and o.get("name"):
        o["first_name"] = o["name"].split()[0]
    if o.get("email") and o["email"] not in o["emails"]:
        o["emails"] = [o["email"]] + o["emails"]
    if not o.get("match"):
        o["match"] = sorted({x.lower() for x in [o.get("first_name", ""), o.get("name", "")] + o["emails"] if x})
    missing = [k for k in ("name", "email") if not o.get(k)] + ([] if cfg["vault"].get("path") else ["vault.path"])
    if missing:
        raise ValueError(f"answers missing: {', '.join(missing)}")
    return cfg


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--preset", required=True, choices=sorted(p.stem for p in PRESETS.glob("[!_]*.json")))
    ap.add_argument("--answers", required=True)
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    try:
        cfg = build(a.preset, json.loads(Path(a.answers).read_text(encoding="utf-8")))
    except ValueError as e:
        print(f"config failed: {e}", file=sys.stderr)
        return 2
    text = json.dumps(cfg, indent=2) + "\n"
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
