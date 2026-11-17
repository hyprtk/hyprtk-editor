"""Search: literal, case, whole word, regex, replace-all and navigation."""

from __future__ import annotations

import unittest

from hyprtk_editor import search
from hyprtk_editor.search import Query

TEXT = "alpha Beta alpha\nGamma alpha beta\nAlpha BETA\n"


class SearchTest(unittest.TestCase):
    def test_literal_is_case_insensitive_by_default(self) -> None:
        matches = search.find_all(TEXT, Query("alpha"))
        self.assertEqual(len(matches), 4)
        self.assertEqual(matches[0], {"start": 0, "length": 5})

    def test_case_sensitive(self) -> None:
        matches = search.find_all(TEXT, Query("alpha", case=True))
        self.assertEqual(len(matches), 3)

    def test_whole_word(self) -> None:
        text = "alpha alphabet alpha"
        self.assertEqual(len(search.find_all(text, Query("alpha", word=True))), 2)

    def test_regex(self) -> None:
        matches = search.find_all(TEXT, Query(r"a\w+a", regex=True, case=True))
        self.assertGreaterEqual(len(matches), 4)

    def test_invalid_regex_returns_nothing(self) -> None:
        self.assertEqual(search.find_all(TEXT, Query("(", regex=True)), [])

    def test_empty_query(self) -> None:
        self.assertEqual(search.find_all(TEXT, Query("")), [])

    def test_find_next_wraps(self) -> None:
        first = search.find_next(TEXT, Query("beta"), 0)
        self.assertEqual(first["start"], 6)
        last = search.find_next(TEXT, Query("beta"), len(TEXT))
        self.assertEqual(last["start"], 6)

    def test_find_backwards(self) -> None:
        match = search.find_next(TEXT, Query("alpha"), 10, backwards=True)
        self.assertEqual(match["start"], 0)

    def test_replace_all_literal_keeps_backslashes(self) -> None:
        new_text, count = search.replace_all("a a a", Query("a"), r"\1")
        self.assertEqual(count, 3)
        self.assertEqual(new_text, r"\1 \1 \1")

    def test_replace_all_regex_groups(self) -> None:
        new_text, count = search.replace_all("key=value", Query(r"(\w+)=(\w+)", regex=True), r"$2=$1")
        self.assertEqual(count, 1)
        self.assertEqual(new_text, "value=key")

    def test_replace_range(self) -> None:
        self.assertEqual(search.replace_range("hello world", 6, 5, "there"), "hello there")


if __name__ == "__main__":
    unittest.main()
