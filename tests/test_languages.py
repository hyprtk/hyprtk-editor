"""Language detection, display names and comment tokens."""

from __future__ import annotations

import unittest

from hyprtk_editor import languages


class LanguagesTest(unittest.TestCase):
    def test_by_extension(self) -> None:
        self.assertEqual(languages.detect("x.py"), "python")
        self.assertEqual(languages.detect("notes.md"), "markdown")
        self.assertEqual(languages.detect("conf.toml"), "toml")
        self.assertEqual(languages.detect("main.rs"), "rust")

    def test_unknown_extension_is_plain_text(self) -> None:
        self.assertEqual(languages.detect("file.zzz"), "text")

    def test_shebang_detection(self) -> None:
        self.assertEqual(languages.detect("script", "#!/usr/bin/env python3"), "python")

    def test_display_names(self) -> None:
        self.assertEqual(languages.display_name("python"), "Python")
        self.assertEqual(languages.display_name("cpp"), "C++")
        self.assertEqual(languages.display_name("qml"), "QML")

    def test_comment_tokens(self) -> None:
        self.assertEqual(languages.comment_tokens("python")[0], "#")
        self.assertEqual(languages.comment_tokens("sql")[0], "--")
        self.assertEqual(languages.comment_tokens("cpp")[0], "//")
        self.assertEqual(languages.comment_tokens("nonsense")[0], "#")

    def test_curated_list_has_no_duplicates(self) -> None:
        aliases = [alias for _, alias in languages.CURATED]
        self.assertEqual(len(aliases), len(set(aliases)))

    def test_generic_conf_is_coloured_only_when_ini_shaped(self) -> None:
        """`.conf` has no Pygments lexer: decide it by content, not by guess."""
        hypr = "$mainMod = SUPER\nmonitor=DP-2,3840x1080@144,0x0,1\nbind = $mainMod, Return, exec, term\n"
        self.assertEqual(languages.detect("hyprland.conf", "", hypr), "ini")
        sectioned = "[server]\nport = 8080\n"
        self.assertEqual(languages.detect("app.conf", "", sectioned), "ini")
        self.assertEqual(languages.detect("settings.cfg", "", "key = value\n"), "ini")
        # A .conf with its own grammar must stay plain rather than be mis-coloured.
        apache = "ServerName example.com\nDocumentRoot /var/www\n"
        self.assertEqual(languages.detect("apache.conf", "", apache), "text")
        self.assertEqual(languages.display_name("ini"), "INI")

    def test_rofi_themes_are_css(self) -> None:
        """Pygments has no rasi lexer; guess_lexer calls it "css+lasso"."""
        self.assertEqual(languages.detect("theme.rasi"), "css")
        self.assertEqual(languages.display_name("css"), "CSS")

    def test_conf_is_read_when_the_caller_has_no_text(self) -> None:
        """The language menu calls detect(path) with no document text."""
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "hyprland.conf"
            path.write_text("$mainMod = SUPER\nbind = $mainMod, Q, killactive\n", encoding="utf-8")
            self.assertEqual(languages.detect(str(path)), "ini")


if __name__ == "__main__":
    unittest.main()
