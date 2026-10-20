#!/usr/bin/env python3
"""Replace one generated block in a file with stdin.

Usage: replace_block.py <file> <name>   (new block content on stdin)
Markers: <!-- block:<name>:start --> … <!-- block:<name>:end -->
Exit 2 (file unchanged) if the file or either marker is missing, duplicated or out of order.
Spec: _system/specs/2026-10-19-weekly-prep-dashboard-design.md §4
"""
import sys
from pathlib import Path


def replace(text, name, content):
    start, end = f"<!-- block:{name}:start -->", f"<!-- block:{name}:end -->"
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError(f"need exactly one '{start}' and one '{end}'")
    i, j = text.index(start) + len(start), text.index(end)
    if j < i:
        raise ValueError(f"'{end}' comes before '{start}'")
    return text[:i] + "\n" + content.strip("\n") + "\n" + text[j:]


def main(argv):
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    path, name = Path(argv[0]), argv[1]
    if not path.is_file():
        print(f"no such file: {path}", file=sys.stderr)
        return 2
    try:
        new = replace(path.read_text(encoding="utf-8"), name, sys.stdin.read())
    except ValueError as e:
        print(f"{path}: {e}", file=sys.stderr)
        return 2
    path.write_text(new, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
