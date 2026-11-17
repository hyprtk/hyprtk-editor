"""File I/O: encoding, BOM, line endings, atomic saves, staleness."""

from __future__ import annotations

import os
import stat
import tempfile
import unittest
from pathlib import Path

from hyprtk_editor import fileio


class FileIoTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_round_trip_lf_utf8(self) -> None:
        path = self.dir / "a.txt"
        result = fileio.write_text(str(path), "one\ntwo\n", "utf-8", "lf", False)
        self.assertTrue(result["ok"])
        loaded = fileio.read_text(str(path))
        self.assertTrue(loaded.ok)
        self.assertEqual(loaded.text, "one\ntwo\n")
        self.assertEqual(loaded.eol, "lf")
        self.assertEqual(loaded.encoding, "utf-8")

    def test_crlf_is_remembered_and_restored(self) -> None:
        path = self.dir / "crlf.txt"
        path.write_bytes(b"one\r\ntwo\r\n")
        loaded = fileio.read_text(str(path))
        self.assertEqual(loaded.text, "one\ntwo\n")
        self.assertEqual(loaded.eol, "crlf")
        fileio.write_text(str(path), loaded.text, loaded.encoding, loaded.eol, loaded.bom)
        self.assertEqual(path.read_bytes(), b"one\r\ntwo\r\n")

    def test_utf8_bom_round_trip(self) -> None:
        path = self.dir / "bom.txt"
        path.write_bytes(b"\xef\xbb\xbfhello")
        loaded = fileio.read_text(str(path))
        self.assertTrue(loaded.bom)
        self.assertEqual(loaded.text, "hello")
        fileio.write_text(str(path), loaded.text, loaded.encoding, loaded.eol, loaded.bom)
        self.assertEqual(path.read_bytes(), b"\xef\xbb\xbfhello")

    def test_cp1252_fallback(self) -> None:
        path = self.dir / "latin.txt"
        path.write_bytes("caf\u00e9".encode("cp1252"))
        loaded = fileio.read_text(str(path))
        self.assertTrue(loaded.ok)
        self.assertEqual(loaded.text, "caf\u00e9")

    def test_stale_write_is_refused(self) -> None:
        path = self.dir / "b.txt"
        first = fileio.write_text(str(path), "v1", "utf-8", "lf", False)
        self.assertTrue(first["ok"])
        stale = fileio.write_text(str(path), "v2", "utf-8", "lf", False, expected_mtime=first["mtime"] - 10)
        self.assertFalse(stale["ok"])
        self.assertTrue(stale.get("stale"))

    def test_atomic_save_keeps_mode(self) -> None:
        path = self.dir / "mode.sh"
        path.write_text("#!/bin/sh\n", encoding="utf-8")
        os.chmod(path, 0o755)
        fileio.write_text(str(path), "#!/bin/sh\necho hi\n", "utf-8", "lf", False)
        self.assertTrue(stat.S_IMODE(os.stat(path).st_mode) & stat.S_IXUSR)
        self.assertEqual(path.read_text(), "#!/bin/sh\necho hi\n")
        self.assertFalse(any(name.endswith(".tmp") for name in os.listdir(self.dir)))

    def test_binary_files_open_read_only(self) -> None:
        path = self.dir / "blob.bin"
        path.write_bytes(b"\x00\x01\x02hello")
        loaded = fileio.read_text(str(path))
        self.assertTrue(loaded.ok)
        self.assertTrue(loaded.binary)
        self.assertTrue(loaded.readonly)

    def test_huge_file_is_refused(self) -> None:
        path = self.dir / "big.txt"
        path.write_text("x" * 100)
        loaded = fileio.read_text(str(path), max_bytes=10)
        self.assertFalse(loaded.ok)
        self.assertIn("too large", loaded.error)

    def test_missing_file_reports_error(self) -> None:
        loaded = fileio.read_text(str(self.dir / "nope.txt"))
        self.assertFalse(loaded.ok)
        self.assertEqual(loaded.error, "File not found")


if __name__ == "__main__":
    unittest.main()
