"""Git gutter: hunk parsing and real-repository status."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from hyprtk_editor import gitdiff

# Real `git diff --unified=0` shapes: a pure insertion has an old count of 0,
# a pure deletion a new count of 0, and a replacement carries both.
DIFF = """diff --git a/app.py b/app.py
index 1111111..2222222 100644
--- a/app.py
+++ b/app.py
@@ -1,0 +2 @@ def top():
+import sys
@@ -10,2 +12,0 @@ def middle():
-removed one
-removed two
@@ -20 +21 @@ def replace():
-x
+y
@@ -31,0 +33,2 @@ def bottom():
+added a
+added b
"""


class ParseDiffTest(unittest.TestCase):
    def test_added_line(self) -> None:
        lines = gitdiff.parse_diff(DIFF)
        self.assertEqual(lines["2"], "add")

    def test_replaced_line_is_a_modification(self) -> None:
        lines = gitdiff.parse_diff(DIFF)
        self.assertEqual(lines["21"], "mod")

    def test_pure_deletion_marks_the_new_side_line(self) -> None:
        lines = gitdiff.parse_diff(DIFF)
        self.assertEqual(lines["12"], "del")

    def test_multi_line_insert_hunk(self) -> None:
        lines = gitdiff.parse_diff(DIFF)
        self.assertEqual(lines["33"], "add")
        self.assertEqual(lines["34"], "add")

    def test_zero_context_deletion(self) -> None:
        lines = gitdiff.parse_diff("@@ -5,2 +4,0 @@\n-a\n-b\n")
        self.assertEqual(lines["4"], "del")

    def test_header_lines_are_ignored(self) -> None:
        lines = gitdiff.parse_diff(DIFF)
        self.assertNotIn("0", lines)
        self.assertTrue(all(int(key) > 0 for key in lines))

    def test_empty_and_garbage_input(self) -> None:
        self.assertEqual(gitdiff.parse_diff(""), {})
        self.assertEqual(gitdiff.parse_diff("not a diff\n@@ nonsense @@\n"), {})

    def test_single_line_hunk_without_counts(self) -> None:
        # git omits ",1", so a missing count must mean one line.
        self.assertEqual(gitdiff.parse_diff("@@ -7 +8 @@\n-a\n+b\n"), {"8": "mod"})


@unittest.skipIf(shutil.which("git") is None, "git is not installed")
class RealRepositoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "Test")
        self.diff = gitdiff.GitDiff()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def git(self, *args: str) -> str:
        done = subprocess.run(
            ["git", *args], cwd=self.root, capture_output=True, text=True, check=True
        )
        return done.stdout

    def write(self, name: str, text: str) -> Path:
        path = self.root / name
        path.write_text(text, encoding="utf-8")
        return path

    def commit_all(self) -> None:
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "snapshot")

    def test_clean_file_has_no_marks(self) -> None:
        path = self.write("clean.txt", "one\ntwo\n")
        self.commit_all()
        status = self.diff.status(str(path))
        self.assertTrue(status.ok)
        self.assertEqual(status.kind, "tracked")
        self.assertEqual(status.lines, {})

    def test_modified_line_is_marked(self) -> None:
        path = self.write("app.py", "one\ntwo\nthree\n")
        self.commit_all()
        path.write_text("one\nCHANGED\nthree\n", encoding="utf-8")
        status = self.diff.status(str(path))
        self.assertEqual(status.lines.get("2"), "mod")

    def test_added_line_is_marked(self) -> None:
        path = self.write("app.py", "one\ntwo\n")
        self.commit_all()
        path.write_text("one\ntwo\nthree\n", encoding="utf-8")
        status = self.diff.status(str(path))
        self.assertEqual(status.lines.get("3"), "add")

    def test_untracked_file_is_all_added(self) -> None:
        path = self.write("new.txt", "a\nb\nc\n")
        status = self.diff.status(str(path))
        self.assertEqual(status.kind, "untracked")
        self.assertEqual(status.lines, {"1": "add", "2": "add", "3": "add"})

    def test_repository_without_commits(self) -> None:
        # No HEAD to diff against yet: the file is simply untracked.
        path = self.write("early.txt", "x\n")
        status = self.diff.status(str(path))
        self.assertTrue(status.ok)
        self.assertEqual(status.kind, "untracked")
        self.assertEqual(status.lines, {"1": "add"})

    def test_outside_a_repository_is_silent(self) -> None:
        with tempfile.TemporaryDirectory() as outside:
            path = Path(outside) / "loose.txt"
            path.write_text("x\n", encoding="utf-8")
            status = self.diff.status(str(path))
            self.assertFalse(status.ok)
            self.assertEqual(status.kind, "none")

    def test_missing_file_is_silent(self) -> None:
        status = self.diff.status(str(self.root / "nope.txt"))
        self.assertFalse(status.ok)

    def test_cache_reuses_the_result_until_the_file_changes(self) -> None:
        path = self.write("app.py", "one\n")
        self.commit_all()
        self.assertTrue(self.diff.status(str(path)).ok)
        path.write_text("one\ntwo\n", encoding="utf-8")
        # Same stat key only when nothing changed; a rewrite must re-run.
        status = self.diff.status(str(path))
        self.assertEqual(status.lines.get("2"), "add")

    def test_invalidate_forces_a_fresh_call(self) -> None:
        path = self.write("app.py", "one\n")
        self.commit_all()
        first = self.diff.status(str(path))
        path.write_text("one\ntwo\n", encoding="utf-8")
        os.utime(path, None)
        self.diff.invalidate(str(path))
        second = self.diff.status(str(path))
        self.assertEqual(first.lines, {})
        self.assertEqual(second.lines.get("2"), "add")


if __name__ == "__main__":
    unittest.main()
