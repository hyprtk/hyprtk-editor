"""Print/PDF rendering: a light-theme document, not the live one."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from hyprtk_editor import printdoc  # noqa: E402

SAMPLE = """#!/usr/bin/env python3
def add(a, b):
    # sum two numbers
    return a + b
"""


class BuildDocumentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_text_survives_a_round_trip(self) -> None:
        document = printdoc.build("one\ntwo\nthree\n", title="notes.txt")
        self.assertIn("one\ntwo\nthree", document.toPlainText())

    def test_title_and_stamp_lead_the_document(self) -> None:
        document = printdoc.build("body\n", title="README.md", stamp="2026-11-17 10:00")
        first = document.toPlainText().split("\n")[0]
        self.assertEqual(first, "README.md")
        self.assertIn("2026-11-17 10:00", document.toPlainText())

    def test_untitled_document_gets_a_heading(self) -> None:
        document = printdoc.build("body\n")
        self.assertTrue(document.toPlainText().startswith("Untitled"))

    def test_blank_lines_are_preserved(self) -> None:
        document = printdoc.build("a\n\n\nb\n")
        self.assertEqual(document.blockCount(), document.blockCount())
        self.assertIn("\n\n\n", document.toPlainText())

    def test_angle_brackets_are_not_markup(self) -> None:
        # The body is inserted with a cursor, never parsed as HTML.
        text = "<script>alert('x')</script> & co\n"
        document = printdoc.build(text)
        self.assertIn(text.strip(), document.toPlainText())

    def test_syntax_colour_is_applied_when_asked(self) -> None:
        document = printdoc.build(SAMPLE, alias="python")
        keyword = document.find("def").charFormat().foreground().color().name()
        comment = document.find("sum two numbers").charFormat().foreground().color().name()
        body = document.find("a + b").charFormat().foreground().color().name()
        self.assertNotEqual(keyword, comment)
        self.assertNotEqual(keyword, body)
        self.assertEqual(comment, printdoc.PRINT_SYNTAX["comment"])

    def test_colour_can_be_switched_off(self) -> None:
        document = printdoc.build(SAMPLE, alias="python", colour=False)
        text = document.toPlainText()
        self.assertIn("return a + b", text)

    def test_empty_text_does_not_crash(self) -> None:
        document = printdoc.build("")
        self.assertGreaterEqual(document.blockCount(), 1)

    def test_long_text_stays_single_pass(self) -> None:
        document = printdoc.build("line\n" * 5000, alias="text")
        self.assertGreater(document.blockCount(), 5000)


class WritePdfTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_pdf_is_written(self) -> None:
        document = printdoc.build(SAMPLE, title="sample.py", alias="python")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.pdf"
            size = printdoc.write_pdf(document, str(path), "sample.py")
            self.assertTrue(path.exists())
            self.assertGreater(size, 500)
            self.assertGreater(len(path.read_bytes()), 500)
            self.assertTrue(path.read_bytes().startswith(b"%PDF"))

    def test_printer_is_configured(self) -> None:
        printer = printdoc.prepare_printer("x")
        self.assertTrue(printer.docName())


if __name__ == "__main__":
    unittest.main()
