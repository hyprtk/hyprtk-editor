"""Pygments span extraction (the highlighter itself needs a display)."""

from __future__ import annotations

import unittest

from hyprtk_editor import highlight

SOURCE = 'def hello(name):\n    # say hi\n    count = 42\n    return "hi " + name\n'


class HighlightTest(unittest.TestCase):
    def test_spans_cover_keyword_string_number_comment(self) -> None:
        spans = highlight.spans(SOURCE, "python")
        styles = {style for line in spans.values() for _, _, style in line}
        for expected in ("keyword", "comment", "string", "number"):
            self.assertIn(expected, styles)

    def test_line_numbers_are_correct(self) -> None:
        spans = highlight.spans(SOURCE, "python")
        self.assertIn(0, spans)
        self.assertIn(1, spans)
        self.assertIn(2, spans)
        comment_line = spans[1]
        self.assertTrue(any(style == "comment" for _, _, style in comment_line))

    def test_plain_text_has_no_spans(self) -> None:
        self.assertEqual(highlight.spans("hello\n", "text"), {})

    def test_unknown_alias_falls_back_to_text(self) -> None:
        self.assertEqual(highlight.spans("hello\n", "not-a-language"), {})

    def test_style_mapping(self) -> None:
        from pygments.token import Comment, Keyword, Name, Number, String

        self.assertEqual(highlight.style_for(Keyword), "keyword")
        self.assertEqual(highlight.style_for(Keyword.Type), "type")
        self.assertEqual(highlight.style_for(Name.Function), "function")
        self.assertEqual(highlight.style_for(String), "string")
        self.assertEqual(highlight.style_for(Number), "number")
        self.assertEqual(highlight.style_for(Comment), "comment")

    def test_huge_documents_are_not_tokenised(self) -> None:
        big = "x" * (highlight.MAX_HIGHLIGHT_CHARS + 1)
        self.assertEqual(highlight.spans(big, "python"), {})


if __name__ == "__main__":
    unittest.main()
