"""The widget-side dialog styling: palette roles and stylesheet."""

from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QPalette  # noqa: E402
from PySide6.QtWidgets import QApplication, QDialogButtonBox, QFileDialog, QListView  # noqa: E402

from hyprtk_editor import dialogs  # noqa: E402
from hyprtk_editor.palette import FALLBACK, resolve  # noqa: E402

PALETTE = {
    "background": "#101018",
    "foreground": "#eeeeee",
    "surface": "#1c1c28",
    "surface_alt": "#2c2c3c",
    "muted": "#888888",
    "accent": "#8ab2ff",
    "accent2": "#22d3ee",
    "danger": "#f38ba8",
    "border": "#3a3a4a",
    "text_on_accent": "#101018",
}


class StyleSheetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_colours_come_from_the_palette(self) -> None:
        sheet = dialogs.style_sheet(PALETTE)
        for key in ("background", "foreground", "surface", "accent", "border"):
            self.assertIn(PALETTE[key], sheet)
        self.assertNotIn("#1e1e2e", sheet)  # the fallback background

    def test_font_is_quoted_and_sized(self) -> None:
        sheet = dialogs.style_sheet(PALETTE, "JetBrainsMono Nerd Font Mono", 15)
        self.assertIn('font-family: "JetBrainsMono Nerd Font Mono"', sheet)
        self.assertIn("font-size: 15px", sheet)

    def test_bad_font_size_falls_back(self) -> None:
        self.assertIn("font-size: 13px", dialogs.style_sheet(PALETTE, "", "big"))
        self.assertIn("font-size: 13px", dialogs.style_sheet(PALETTE, "", None))
        self.assertIn("font-size: 8px", dialogs.style_sheet(PALETTE, "", 0))
        self.assertIn("font-size: 48px", dialogs.style_sheet(PALETTE, "", 999))

    def test_missing_keys_use_the_fallback_palette(self) -> None:
        sheet = dialogs.style_sheet({})
        self.assertIn(FALLBACK["background"], sheet)
        self.assertIn(FALLBACK["accent"], sheet)

    def test_palette_roles(self) -> None:
        pal = dialogs.qpalette(PALETTE)
        self.assertEqual(pal.color(QPalette.Window).name(), PALETTE["background"])
        self.assertEqual(pal.color(QPalette.Text).name(), PALETTE["foreground"])
        self.assertEqual(pal.color(QPalette.Base).name(), PALETTE["surface"])
        self.assertEqual(pal.color(QPalette.Highlight).name(), PALETTE["accent"])
        self.assertEqual(pal.color(QPalette.HighlightedText).name(), PALETTE["text_on_accent"])
        self.assertEqual(pal.color(QPalette.Disabled, QPalette.Text).name(), PALETTE["muted"])

    def test_real_palette_is_accepted(self) -> None:
        pal = resolve()
        sheet = dialogs.style_sheet(pal, "monospace", 13)
        self.assertIn(pal["background"], sheet)
        self.assertIsInstance(dialogs.qpalette(pal), QPalette)

    def test_apply_styles_the_dialog_and_its_accept_button(self) -> None:
        dialog = QFileDialog(None, "Open File", "/tmp", "All files (*)")
        try:
            dialogs.apply(dialog, PALETTE, "monospace", 13)
            self.assertIn(PALETTE["background"], dialog.styleSheet())
            self.assertEqual(dialog.palette().color(QPalette.Window).name(),
                             PALETTE["background"])
            box = dialog.findChild(QDialogButtonBox)
            primary = [b for b in box.buttons() if b.property("primary")]
            self.assertEqual(len(primary), 1)
            self.assertTrue(primary[0].isDefault())
        finally:
            dialog.deleteLater()

    def test_themed_dialog_dresses_itself_and_drops_the_theme_icons(self) -> None:
        dialog = dialogs.ThemedFileDialog(PALETTE, "monospace", 13)
        dialog.setFileMode(QFileDialog.ExistingFiles)
        try:
            dialog.show()
            for _ in range(5):
                self.app.processEvents()
            self.assertIn(PALETTE["background"], dialog.styleSheet())
            box = dialog.findChild(QDialogButtonBox)
            self.assertTrue(box.buttons())
            self.assertEqual([b.text() for b in box.buttons() if not b.icon().isNull()], [])
            primary = [b for b in box.buttons() if b.property("primary")]
            self.assertEqual(len(primary), 1)
            self.assertIn("primary", dialog.styleSheet())
        finally:
            dialog.close()
            dialog.deleteLater()

    def test_native_dialog_is_refused(self) -> None:
        # The native GTK chooser ignores the palette, so it must never be used.
        dialog = dialogs.ThemedFileDialog(PALETTE, "monospace", 13)
        try:
            self.assertTrue(dialog.testOption(QFileDialog.DontUseNativeDialog))
        finally:
            dialog.deleteLater()

    def test_long_filter_does_not_stretch_the_dialog(self) -> None:
        from hyprtk_editor.bridge import OPEN_FILTER

        dialog = dialogs.ThemedFileDialog(PALETTE, "monospace", 13)
        try:
            dialog.setNameFilter(OPEN_FILTER)
            dialog.setFileMode(QFileDialog.ExistingFiles)
            self.assertLess(dialog.sizeHint().width(), 1000)
            sidebar = dialog.findChild(QListView, "sidebar")
            if sidebar is not None:
                self.assertGreaterEqual(sidebar.minimumWidth(), 170)
        finally:
            dialog.deleteLater()


if __name__ == "__main__":
    unittest.main()
