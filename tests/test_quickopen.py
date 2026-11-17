"""Quick open: fuzzy scoring and the candidate list behind Ctrl+P."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from hyprtk_editor import search  # noqa: E402
from hyprtk_editor.bridge import Bridge  # noqa: E402


class FuzzyScoreTest(unittest.TestCase):
    def test_subsequence_matches(self) -> None:
        self.assertIsNotNone(search.fuzzy_score("mn", "main.py"))
        self.assertIsNotNone(search.fuzzy_score("mnp", "main_window.py"))

    def test_missing_character_does_not_match(self) -> None:
        self.assertIsNone(search.fuzzy_score("xyz", "main.py"))

    def test_order_matters(self) -> None:
        self.assertIsNone(search.fuzzy_score("pym", "main.py"))

    def test_empty_needle_matches_everything(self) -> None:
        self.assertEqual(search.fuzzy_score("", "anything"), 0)

    def test_empty_haystack_only_matches_an_empty_needle(self) -> None:
        self.assertIsNone(search.fuzzy_score("a", ""))

    def test_case_insensitive(self) -> None:
        self.assertIsNotNone(search.fuzzy_score("MAIN", "main.py"))

    def test_adjacency_beats_scattering(self) -> None:
        tight = search.fuzzy_score("main", "main.py")
        loose = search.fuzzy_score("main", "m_a_i_n_long_name.py")
        self.assertGreater(tight, loose)

    def test_word_start_beats_mid_word(self) -> None:
        start = search.fuzzy_score("win", "main_window.py")
        middle = search.fuzzy_score("win", "mainwinning.py")
        self.assertGreater(start, middle)

    def test_shorter_candidate_wins_a_tie(self) -> None:
        short = search.fuzzy_score("main", "main.py")
        long = search.fuzzy_score("main", "main_window_test.py")
        self.assertGreater(short, long)


class RankTest(unittest.TestCase):
    def setUp(self) -> None:
        self.items = [
            {"name": "window.py", "path": "/a/window.py"},
            {"name": "main.py", "path": "/a/main.py"},
            {"name": "notes.md", "path": "/a/notes.md"},
        ]

    def test_best_match_first(self) -> None:
        ranked = search.rank(self.items, "main")
        self.assertEqual(ranked[0]["name"], "main.py")

    def test_non_matches_are_dropped(self) -> None:
        ranked = search.rank(self.items, "main")
        self.assertEqual([item["name"] for item in ranked], ["main.py"])

    def test_empty_query_keeps_the_input_order(self) -> None:
        ranked = search.rank(self.items, "")
        self.assertEqual([item["name"] for item in ranked],
                         ["window.py", "main.py", "notes.md"])

    def test_limit_applies(self) -> None:
        self.assertEqual(len(search.rank(self.items, "", limit=2)), 2)

    def test_path_is_used_as_a_fallback_key(self) -> None:
        ranked = search.rank([{"name": "x.txt", "path": "/deep/target.txt"}], "target")
        self.assertEqual(len(ranked), 1)

    def test_garbage_rows_are_ignored(self) -> None:
        self.assertEqual(search.rank([None, "nope", {"name": "main.py", "path": ""}], "main"),
                         [{"name": "main.py", "path": ""}])


class QuickOpenBridgeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        os.environ["XDG_CONFIG_HOME"] = str(root / "config")
        os.environ["XDG_CACHE_HOME"] = str(root / "cache")
        os.environ["XDG_STATE_HOME"] = str(root / "state")
        self.bridge = Bridge()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write(self, name: str, text: str = "x\n") -> str:
        path = Path(self.tmp.name) / name
        path.write_text(text, encoding="utf-8")
        return str(path)

    def test_current_folder_files_are_listed(self) -> None:
        alpha = self.write("alpha.txt")
        beta = self.write("beta.py")
        paths = [item["path"] for item in self.bridge.quickOpen(alpha)]
        self.assertIn(alpha, paths)
        self.assertIn(beta, paths)

    def test_hidden_and_directory_entries_are_skipped(self) -> None:
        self.write(".secret.txt")
        (Path(self.tmp.name) / "subdir").mkdir()
        paths = [item["path"] for item in self.bridge.quickOpen(str(Path(self.tmp.name) / "x.txt"))]
        self.assertFalse(any(".secret" in path for path in paths))
        self.assertFalse(any(path.endswith("subdir") for path in paths))

    def test_recent_files_come_first(self) -> None:
        self.write("alpha.txt")
        recent = self.write("recent.txt")
        self.bridge.addRecent(recent)
        paths = [item["path"] for item in self.bridge.quickOpen(str(Path(self.tmp.name) / "alpha.txt"))]
        self.assertEqual(paths[0], recent)
        self.assertEqual(self.bridge.quickOpen(recent)[0]["source"], "recent")

    def test_manual_entry_shape(self) -> None:
        path = self.write("alpha.txt")
        entry = self.bridge.quickOpen(path)[0]
        self.assertEqual(set(entry), {"path", "name", "folder", "source"})
        self.assertEqual(entry["name"], "alpha.txt")
        self.assertEqual(entry["folder"], self.tmp.name)

    def test_rank_files_returns_the_best_match(self) -> None:
        candidates = [
            {"name": "window.py", "path": "/a/window.py"},
            {"name": "main.py", "path": "/a/main.py"},
        ]
        ranked = self.bridge.rankFiles(candidates, "mai")
        self.assertEqual(ranked[0]["name"], "main.py")


if __name__ == "__main__":
    unittest.main()
