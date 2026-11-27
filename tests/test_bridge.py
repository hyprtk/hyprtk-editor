"""The QML facade: documents, saving, search, line ops, settings, drafts."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from unittest import mock  # noqa: E402

from PySide6.QtGui import QGuiApplication, QPalette, QWindow  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication, QFileDialog  # noqa: E402

from hyprtk_editor.bridge import Bridge  # noqa: E402


class BridgeTest(unittest.TestCase):
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

    def write(self, name: str, text: str) -> str:
        path = Path(self.tmp.name) / name
        path.write_text(text, encoding="utf-8")
        return str(path)

    def test_load_detects_language_and_title(self) -> None:
        path = self.write("hello.py", "print('hi')\n")
        data = self.bridge.load(path)
        self.assertTrue(data["ok"])
        self.assertEqual(data["language"], "python")
        self.assertEqual(data["languageName"], "Python")
        self.assertEqual(data["title"], "hello.py")
        self.assertEqual(data["text"], "print('hi')\n")

    def test_new_ids_are_unique(self) -> None:
        self.assertNotEqual(self.bridge.newId(), self.bridge.newId())

    def test_save_round_trip(self) -> None:
        path = Path(self.tmp.name) / "out.txt"
        result = self.bridge.save(str(path), "hello\n", "utf-8", "lf", False, 0)
        self.assertTrue(result["ok"])
        self.assertEqual(path.read_text(), "hello\n")
        self.assertIn(str(path), self.bridge.settings.get("recent"))

    def test_save_is_refused_when_the_file_moved_on(self) -> None:
        path = Path(self.tmp.name) / "out.txt"
        path.write_text("old", encoding="utf-8")
        result = self.bridge.save(str(path), "new", "utf-8", "lf", False, 12345.0)
        self.assertFalse(result["ok"])
        self.assertTrue(result.get("stale"))

    def test_line_op(self) -> None:
        result = self.bridge.lineOp("a\n", 0, 0, "duplicate", "#", 4, True)
        self.assertEqual(result["text"], "a\na\n")

    def test_search_and_replace(self) -> None:
        matches = self.bridge.findAll("a b a", "a", False, False, False)
        self.assertEqual(len(matches), 2)
        replaced = self.bridge.replaceAll("a b a", "a", "c", False, False, False)
        self.assertEqual(replaced["count"], 2)
        self.assertEqual(replaced["text"], "c b c")

    def test_stats(self) -> None:
        data = self.bridge.stats("one two", 0, 0)
        self.assertEqual(data["words"], 2)
        self.assertEqual(data["bytesHuman"], "7 B")

    def test_bracket_match(self) -> None:
        text = "def f(a, [b]):\n    return (a)\n"
        opening = text.index("(")
        result = self.bridge.bracketMatch(text, opening + 1)
        self.assertTrue(result["ok"])
        self.assertEqual(result["positions"][0], [0, opening])
        self.assertEqual(result["positions"][1], [0, text.index(")")])

    def test_bracket_match_without_a_pair(self) -> None:
        self.assertFalse(self.bridge.bracketMatch("hello", 2)["ok"])

    def test_comment_prefix(self) -> None:
        self.assertEqual(self.bridge.commentPrefix("python"), "#")
        self.assertEqual(self.bridge.commentPrefix("sql"), "--")

    def test_detect(self) -> None:
        self.assertEqual(self.bridge.detect("x.rs", "")["name"], "Rust")

    def test_load_colours_ini_shaped_conf_and_rofi_themes(self) -> None:
        conf = self.write("hyprland.conf", "$mainMod = SUPER\nbind = $mainMod, Q, killactive\n")
        data = self.bridge.load(conf)
        self.assertEqual(data["language"], "ini")
        self.assertEqual(data["languageName"], "INI")

        rasi = self.write("theme.rasi", "window { width: 400px; }\n")
        data = self.bridge.load(rasi)
        self.assertEqual(data["language"], "css")
        self.assertEqual(data["languageName"], "CSS")

    def test_settings_persist(self) -> None:
        self.bridge.updateSettings({"font_size": 17, "wrap": True})
        config = Path(os.environ["XDG_CONFIG_HOME"]) / "hyprtk-editor" / "config.json"
        data = json.loads(config.read_text())
        self.assertEqual(data["font_size"], 17)
        self.assertTrue(data["wrap"])
        self.assertEqual(self.bridge.settings.get("font_size"), 17)

    def test_drafts_round_trip(self) -> None:
        self.bridge.saveDraft("doc1", "/tmp/x.txt", "x.txt", "unsaved")
        self.assertEqual(self.bridge.loadDraft("doc1")["text"], "unsaved")
        self.assertEqual(len(self.bridge.drafts), 1)
        self.bridge.clearDraft("doc1")
        self.assertEqual(self.bridge.drafts, [])

    def test_session_round_trip(self) -> None:
        self.bridge.saveSession({"active": "a", "docs": [{"id": "a", "path": "/tmp/x"}]})
        loaded = self.bridge.loadSession()
        self.assertEqual(loaded["active"], "a")
        self.assertEqual(len(loaded["docs"]), 1)

    def test_palette_exposes_colors(self) -> None:
        palette = self.bridge.palette
        self.assertTrue(palette["background"].isValid())
        self.assertTrue(palette["syntax"]["comment"].isValid())

    def test_git_status_shape(self) -> None:
        # Outside a repository the gutter gets a well-formed "nothing" answer
        # rather than an exception or a half-filled map.
        loose = str(Path(self.tmp.name) / "loose.txt")
        status = self.bridge.gitStatus(loose)
        # The gutter is filled by a worker; the first call returns what is
        # cached (nothing) and the answer arrives on gitChanged.
        waited = 0
        while not status and waited < 3000:
            QTest.qWait(25)
            waited += 25
            status = self.bridge.gitStatus(loose)
        self.assertEqual(set(status), {"ok", "repo", "kind", "lines", "error"})
        self.assertFalse(status["ok"])
        self.assertEqual(status["kind"], "none")

    def test_write_pdf_uses_the_pane_text(self) -> None:
        from PySide6.QtGui import QTextDocument

        document = QTextDocument()
        document.setPlainText("alpha\nbeta\n")

        class FakePane:
            alias = "text"
            path = str(Path(self.tmp.name) / "notes.txt")

            def __init__(self, doc: QTextDocument) -> None:
                self.document = doc

        self.bridge._editors["doc"] = FakePane(document)
        target = str(Path(self.tmp.name) / "out.pdf")
        result = self.bridge.writePdf("doc", target)
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["path"], target)
        self.assertGreater(result["bytes"], 500)

    def test_write_pdf_without_a_document(self) -> None:
        self.assertFalse(self.bridge.writePdf("missing", str(Path(self.tmp.name) / "x.pdf"))["ok"])

    def test_export_pdf_cancel_writes_nothing(self) -> None:
        from PySide6.QtGui import QTextDocument

        document = QTextDocument()
        document.setPlainText("alpha\n")

        class FakePane:
            alias = "text"
            path = ""

            def __init__(self, doc: QTextDocument) -> None:
                self.document = doc

        self.bridge._editors["doc"] = FakePane(document)
        with mock.patch.object(self.bridge, "_save_dialog", return_value=""):
            result = self.bridge.exportPdf("doc")
        self.assertFalse(result["ok"])
        self.assertTrue(result["cancelled"])


class FileDialogTest(unittest.TestCase):
    """The dialogs must exist, be children of the editor and return paths.

    Regression: they used ``QGuiApplication.activeWindow()``, which does not
    exist, so Ctrl+O, Save As and Open Folder all died with an AttributeError
    before a dialog ever appeared.
    """

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

    def test_dialog_is_transient_child_of_editor_window(self) -> None:
        window = QWindow()
        window.show()
        self.app.processEvents()
        focused = QGuiApplication.focusWindow()
        if focused is None:
            window.deleteLater()
            self.skipTest("no focus window under this platform")
        dialog = self.bridge._file_dialog("Open File", self.tmp.name,
                                          QFileDialog.ExistingFiles)
        try:
            self.assertIsInstance(dialog, QFileDialog)
            self.assertEqual(dialog.fileMode(), QFileDialog.ExistingFiles)
            self.assertIs(dialog.windowHandle().transientParent(), focused)
        finally:
            dialog.close()
            dialog.deleteLater()
            window.close()
            window.deleteLater()

    def test_dialogs_use_the_editor_palette(self) -> None:
        dialog = self.bridge._file_dialog("Open File", self.tmp.name,
                                          QFileDialog.ExistingFiles)
        try:
            background = self.bridge._palette["background"]
            self.assertTrue(background.startswith("#"))
            self.assertIn(background, dialog.styleSheet())
            self.assertEqual(dialog.palette().color(QPalette.Window).name(), background)
        finally:
            dialog.close()
            dialog.deleteLater()

    def test_open_dialog_returns_selected_files(self) -> None:
        chosen = self.write("picked.txt")
        with mock.patch.object(QFileDialog, "exec", return_value=QFileDialog.Accepted), \
                mock.patch.object(QFileDialog, "selectedFiles", return_value=[chosen]):
            self.assertEqual(self.bridge.openDialog(), [chosen])
        self.assertEqual(self.bridge.settings.get("last_open_dir"), self.tmp.name)

    def test_open_dialog_cancel_returns_nothing(self) -> None:
        with mock.patch.object(QFileDialog, "exec", return_value=QFileDialog.Rejected):
            self.assertEqual(self.bridge.openDialog(), [])

    def test_save_dialog_cancel_returns_empty_string(self) -> None:
        with mock.patch.object(QFileDialog, "exec", return_value=QFileDialog.Rejected):
            self.assertEqual(self.bridge.saveDialog("notes.txt"), "")

    def test_folder_dialog_returns_the_chosen_folder(self) -> None:
        with mock.patch.object(QFileDialog, "exec", return_value=QFileDialog.Accepted), \
                mock.patch.object(QFileDialog, "selectedFiles", return_value=[self.tmp.name]):
            self.assertEqual(self.bridge.folderDialog(self.tmp.name), self.tmp.name)

    def test_qml_containers_arrive_as_qjsvalue(self) -> None:
        """A QVariant slot is handed JS containers as an opaque QJSValue.

        PySide6 6.12 passes every object *and* array that way, so a slot that
        iterates or isinstance-checks its argument fails while QML prints a
        TypeError and carries on. These four slots are the ones that cross the
        boundary with a container, and the failure mode is invisible in the UI:
        search highlights, bracket matching, every setting write and the saved
        session silently do nothing.
        """
        from PySide6.QtQml import QJSEngine

        js = QJSEngine()

        class Recorder:
            def __init__(self) -> None:
                self.search = None
                self.brackets = None

            def set_search(self, values) -> None:
                self.search = values

            def set_brackets(self, positions) -> None:
                self.brackets = positions

        class FakePane:
            alias = "text"

            def __init__(self) -> None:
                self.highlighter = Recorder()

        pane = FakePane()
        self.bridge._editors["doc"] = pane

        # The exact call that used to abort a tab activation: an empty array.
        self.bridge.setSearch("doc", js.evaluate("[]"))
        self.assertEqual(pane.highlighter.search, [])

        self.bridge.setSearch("doc", js.evaluate("[{start: 2, length: 3}, {start: 9, length: 1, current: true}]"))
        self.assertEqual(pane.highlighter.search, [(2, 3, False), (9, 1, True)])

        self.bridge.setBrackets("doc", js.evaluate("({ok: true, positions: [[1, 4], [2, 0]]})"))
        self.assertEqual(pane.highlighter.brackets, [[1, 4], [2, 0]])

        self.bridge.updateSettings(js.evaluate("({font_size: 21})"))
        self.assertEqual(self.bridge.config.get("font_size"), 21)

        self.bridge.saveSession(js.evaluate("({active: 'doc', docs: []})"))
        self.assertEqual(self.bridge.session.load().get("active"), "doc")

    def write(self, name: str, text: str = "x\n") -> str:
        path = Path(self.tmp.name) / name
        path.write_text(text, encoding="utf-8")
        return str(path)


if __name__ == "__main__":
    unittest.main()
