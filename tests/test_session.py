"""Session persistence and crash-recovery drafts."""

from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from hyprtk_editor.session import Drafts, Session


class SessionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_round_trip_and_sanitising(self) -> None:
        session = Session(self.root / "session.json")
        session.save({
            "active": "abc",
            "docs": [
                {"id": "abc", "path": "/tmp/a.txt", "cursor": 12, "scroll": 3.5, "language": "python"},
                {"id": "", "path": "/tmp/skip.txt"},
                "nonsense",
            ],
        })
        loaded = session.load()
        self.assertEqual(loaded["active"], "abc")
        self.assertEqual(len(loaded["docs"]), 1)
        self.assertEqual(loaded["docs"][0]["cursor"], 12)
        self.assertEqual(loaded["docs"][0]["scroll"], 3.5)

    def test_missing_session_is_empty(self) -> None:
        loaded = Session(self.root / "nope.json").load()
        self.assertEqual(loaded, {"docs": [], "active": ""})

    def test_corrupt_session_is_empty(self) -> None:
        path = self.root / "bad.json"
        path.write_text("{not json", encoding="utf-8")
        self.assertEqual(Session(path).load()["docs"], [])

    def test_session_clear(self) -> None:
        path = self.root / "session.json"
        session = Session(path)
        session.save({"active": "a", "docs": [{"id": "a", "path": "x"}]})
        session.clear()
        self.assertFalse(path.exists())


class DraftsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.drafts = Drafts(Path(self.tmp.name) / "drafts")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_save_load_clear(self) -> None:
        self.drafts.save("id1", "/tmp/a.txt", "a.txt", "hello")
        loaded = self.drafts.load("id1")
        self.assertEqual(loaded["text"], "hello")
        self.assertEqual(len(self.drafts.list()), 1)
        self.drafts.clear("id1")
        self.assertIsNone(self.drafts.load("id1"))
        self.assertEqual(self.drafts.list(), [])

    def test_saving_twice_keeps_one_index_entry(self) -> None:
        self.drafts.save("id1", "", "Untitled", "one")
        self.drafts.save("id1", "", "Untitled", "two")
        self.assertEqual(len(self.drafts.list()), 1)
        self.assertEqual(self.drafts.load("id1")["text"], "two")

    def test_unknown_draft(self) -> None:
        self.assertIsNone(self.drafts.load("missing"))

    def test_old_drafts_are_pruned(self) -> None:
        self.drafts.save("old", "", "old", "x")
        index = self.drafts._index()
        index[0]["ts"] = time.time() - 40 * 86400
        self.drafts._write_index(index)
        self.assertEqual(self.drafts.list(max_age_days=30), [])

    def test_ids_are_sanitised(self) -> None:
        self.drafts.save("../../etc/passwd", "", "x", "y")
        self.assertEqual(len(self.drafts.list()), 1)


if __name__ == "__main__":
    unittest.main()
