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


if __name__ == "__main__":
    unittest.main()
