#!/usr/bin/env python3
"""Tests for _system/tools/replace_block.py. Run: python3 -m unittest _system/tests/test_replace_block.py -v"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / "tools" / "replace_block.py"
HOME = ("# Home\n\n<!-- block:today:start -->\nold today\n<!-- block:today:end -->\n\n## Keep\nmine\n\n"
        "<!-- block:this-week:start -->\n<!-- block:this-week:end -->\n")


class ReplaceBlockTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.file = Path(self.tmp.name) / "home.md"
        self.file.write_text(HOME, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def run_tool(self, name, content, *extra):
        return subprocess.run([sys.executable, str(TOOL), str(self.file), name, *extra], input=content,
                              capture_output=True, text=True)

    def test_replaces_between_markers_and_keeps_rest(self):
        r = self.run_tool("today", "\n- new line\n\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.file.read_text(encoding="utf-8"), HOME.replace("old today", "- new line"))

    def test_fills_empty_block(self):
        self.assertEqual(self.run_tool("this-week", "TL;DR").returncode, 0)
        self.assertIn("<!-- block:this-week:start -->\nTL;DR\n<!-- block:this-week:end -->",
                      self.file.read_text(encoding="utf-8"))

    def test_missing_markers_fail_unchanged(self):
        r = self.run_tool("nope", "x")
        self.assertEqual(r.returncode, 2)
        self.assertIn("block:nope:start", r.stderr)
        self.assertEqual(self.file.read_text(encoding="utf-8"), HOME)

    def test_duplicate_or_reversed_markers_fail(self):
        self.file.write_text(HOME + "<!-- block:today:start -->\n", encoding="utf-8")
        self.assertEqual(self.run_tool("today", "x").returncode, 2)
        self.file.write_text("<!-- block:x:end -->\n<!-- block:x:start -->\n", encoding="utf-8")
        self.assertEqual(self.run_tool("x", "y").returncode, 2)

    def test_missing_file_or_args_fail(self):
        r = subprocess.run([sys.executable, str(TOOL), str(self.file) + ".nope", "today"], input="x",
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertEqual(self.run_tool("today", "x", "extra").returncode, 2)


if __name__ == "__main__":
    unittest.main()
