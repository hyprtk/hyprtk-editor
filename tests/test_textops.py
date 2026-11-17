"""Line operations return both the new text and the new selection."""

from __future__ import annotations

import unittest

from hyprtk_editor import textops


class TextOpsTest(unittest.TestCase):
    def test_duplicate_line(self) -> None:
        result = textops.duplicate("a\nb\nc\n", 2, 2)
        self.assertEqual(result["text"], "a\nb\nb\nc\n")
        self.assertEqual((result["selStart"], result["selEnd"]), (4, 6))

    def test_move_up_swaps_with_previous_line(self) -> None:
        result = textops.move_up("a\nb\nc\n", 2, 2)
        self.assertEqual(result["text"], "b\na\nc\n")
        self.assertEqual((result["selStart"], result["selEnd"]), (0, 2))

    def test_move_down_swaps_with_next_line(self) -> None:
        result = textops.move_down("a\nb\nc\n", 2, 2)
        self.assertEqual(result["text"], "a\nc\nb\n")
        self.assertEqual((result["selStart"], result["selEnd"]), (4, 6))

    def test_move_up_at_top_is_a_noop(self) -> None:
        result = textops.move_up("a\nb\n", 0, 0)
        self.assertEqual(result["text"], "a\nb\n")

    def test_delete_lines(self) -> None:
        result = textops.delete_lines("a\nb\nc\n", 2, 2)
        self.assertEqual(result["text"], "a\nc\n")

    def test_toggle_comment_adds_and_removes(self) -> None:
        original = "x = 1\n  y = 2\n"
        added = textops.toggle_comment(original, 0, len(original), "#")
        self.assertEqual(added["text"], "# x = 1\n  # y = 2\n")
        removed = textops.toggle_comment(added["text"], 0, len(added["text"]), "#")
        self.assertEqual(removed["text"], original)

    def test_toggle_comment_without_selection_hits_the_current_line(self) -> None:
        result = textops.toggle_comment("a\nb\n", 2, 2, "#")
        self.assertEqual(result["text"], "a\n# b\n")

    def test_toggle_comment_ignores_blank_lines(self) -> None:
        result = textops.toggle_comment("a\n\nb\n", 0, 5, "//")
        self.assertEqual(result["text"], "// a\n\n// b\n")

    def test_sort_lines(self) -> None:
        self.assertEqual(textops.sort_lines("b\na\nc\n", 0, 0)["text"], "a\nb\nc\n")

    def test_sort_lines_descending_and_unique(self) -> None:
        text = "b\na\nb\n"
        self.assertEqual(textops.sort_lines(text, 0, 0, reverse=True)["text"], "b\nb\na\n")
        self.assertEqual(textops.sort_lines(text, 0, 0, unique=True)["text"], "a\nb\n")

    def test_trim_trailing_whitespace(self) -> None:
        self.assertEqual(textops.trim_trailing("a  \nb\t\nc", 0, 0)["text"], "a\nb\nc")

    def test_indent_and_outdent(self) -> None:
        indented = textops.indent("a\nb\n", 0, 4, 2, True)
        self.assertEqual(indented["text"], "  a\n  b\n")
        self.assertEqual(textops.outdent(indented["text"], 0, 8, 2, True)["text"], "a\nb\n")

    def test_join_lines(self) -> None:
        self.assertEqual(textops.join_lines("a\nb\nc\n", 0, 5)["text"], "a b c\n")

    def test_change_case(self) -> None:
        self.assertEqual(textops.change_case("abc", 0, 0, "upper")["text"], "ABC")
        self.assertEqual(textops.change_case("ABC", 0, 0, "lower")["text"], "abc")
        self.assertEqual(textops.change_case("hello world", 0, 0, "title")["text"], "Hello World")

    def test_convert_indent(self) -> None:
        self.assertEqual(textops.convert_indent("\ta\n", 0, 0, True, 4)["text"], "    a\n")
        self.assertEqual(textops.convert_indent("    a\n", 0, 0, False, 4)["text"], "\ta\n")

    def test_stats(self) -> None:
        data = textops.stats("one two\nthree", 0, 0)
        self.assertEqual(data["chars"], 13)
        self.assertEqual(data["words"], 3)
        self.assertEqual(data["lines"], 2)
        self.assertEqual(data["bytes"], 13)

    def test_apply_dispatch(self) -> None:
        self.assertEqual(textops.apply("a\n", 0, 0, "duplicate")["text"], "a\na\n")
        self.assertEqual(textops.apply("a\n", 0, 0, "unknown")["text"], "a\n")


if __name__ == "__main__":
    unittest.main()
