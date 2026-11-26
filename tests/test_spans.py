"""Off-thread tokenising: late results apply, superseded ones do not."""

from __future__ import annotations

import os
import threading
import tempfile
import unittest
from pathlib import Path
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QTextDocument  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

import hyprtk_editor.bridge as bridge_module  # noqa: E402
from hyprtk_editor.bridge import Attached, Bridge  # noqa: E402

BIG = "def f(x):\n    return x + 1  # comment\n" * 1200   # ~40 KB, over the inline limit
SMALL = "def f(x):\n    return x\n"


class FakeHighlighter:
    def __init__(self) -> None:
        self.enabled = True
        self.spans = {}
        self.applied = 0
        self.current_line = 0

    def set_spans(self, value) -> None:
        self.spans = value
        self.applied += 1

    def set_enabled(self, value) -> None:
        self.enabled = bool(value)

    def set_current_line(self, line) -> None:
        self.current_line = int(line)

    def rehighlightBlock(self, block) -> None:  # noqa: N802 - Qt name
        pass

    def setDocument(self, document) -> None:  # noqa: N802 - Qt name
        pass

    def deleteLater(self) -> None:  # noqa: N802 - Qt name
        pass


class TokenisingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])
        # Never read the developer's own config: "syntax": false there would
        # turn every one of these into the "syntax off" branch.
        cls._tmp = tempfile.TemporaryDirectory()
        os.environ["XDG_CONFIG_HOME"] = str(Path(cls._tmp.name) / "config")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def setUp(self) -> None:
        self.bridge = Bridge()

    def tearDown(self) -> None:
        self.bridge._shutdown()

    def attach(self, text: str) -> FakeHighlighter:
        document = QTextDocument()
        document.setPlainText(text)
        highlighter = FakeHighlighter()
        self.bridge._editors["doc"] = Attached(
            area=None, qdoc=None, document=document, highlighter=highlighter, alias="python"
        )
        return highlighter

    def wait_for(self, predicate, timeout_ms: int = 4000) -> bool:
        waited = 0
        while waited < timeout_ms:
            if predicate():
                return True
            QTest.qWait(25)
            waited += 25
        return predicate()

    def test_small_file_is_tokenised_inline(self) -> None:
        highlighter = self.attach(SMALL)
        self.bridge.recompute("doc", 0, 5)
        self.assertEqual(highlighter.applied, 1)
        self.assertTrue(highlighter.spans)

    def test_large_file_returns_before_tokenising(self) -> None:
        highlighter = self.attach(BIG)
        self.bridge.recompute("doc", 0, 5)
        self.assertEqual(highlighter.applied, 0)
        self.assertTrue(self.wait_for(lambda: highlighter.applied == 1))
        self.assertTrue(highlighter.spans)

    def test_superseded_result_is_dropped(self) -> None:
        highlighter = self.attach(BIG)
        gate = threading.Event()
        calls: list[int] = []

        def slow(text: str, alias: str):
            calls.append(len(calls) + 1)
            if len(calls) == 1:
                gate.wait(3)
            return {"call": len(calls)}

        with mock.patch.object(bridge_module, "spans", slow):
            self.bridge.recompute("doc", 0, 5)   # generation 1, held in the worker
            self.bridge.recompute("doc", 0, 5)   # generation 2, queued behind it
            QTest.qWait(50)
            gate.set()
            self.assertTrue(self.wait_for(lambda: highlighter.applied >= 1))
            QTest.qWait(150)

        self.assertEqual(highlighter.applied, 1)
        self.assertEqual(highlighter.spans.get("call"), 2)

    def test_result_for_a_detached_document_is_dropped(self) -> None:
        highlighter = self.attach(BIG)
        gate = threading.Event()

        def slow(text: str, alias: str):
            gate.wait(3)
            return {0: [(0, 3, "keyword")]}

        with mock.patch.object(bridge_module, "spans", slow):
            self.bridge.recompute("doc", 0, 5)
            self.bridge.detach("doc")
            gate.set()
            QTest.qWait(200)

        self.assertEqual(highlighter.applied, 0)

    def test_syntax_off_disables_highlighting(self) -> None:
        highlighter = self.attach(SMALL)
        self.bridge.settings.update({"syntax": False})
        self.bridge.recompute("doc", 0, 5)
        self.assertFalse(highlighter.enabled)
        self.assertEqual(highlighter.spans, {})

    def test_oversized_file_is_not_tokenised(self) -> None:
        highlighter = self.attach("x" * 450_000)
        self.bridge.recompute("doc", 0, 5)
        self.assertFalse(highlighter.enabled)
        self.assertEqual(highlighter.spans, {})


if __name__ == "__main__":
    unittest.main()
