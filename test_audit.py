"""Tests use temporary repositories and require only the standard library."""

import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from taraw.audit import audit_repository
from taraw.cli import main


class AuditTests(unittest.TestCase):
    def test_finds_notes_whitespace_and_missing_docs(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "app.py").write_text("# TODO: refine\nprint('hello')  \n# fixme check\n", encoding="utf-8")
            report = audit_repository(root)
            summary = [(f.rule, f.path, f.line) for f in report.findings]
            self.assertIn(("missing_readme", ".", None), summary)
            self.assertIn(("missing_license", ".", None), summary)
            self.assertIn(("developer_note", "app.py", 1), summary)
            self.assertIn(("trailing_whitespace", "app.py", 2), summary)
            self.assertIn(("developer_note", "app.py", 3), summary)
            self.assertEqual(report.files_checked, 1)

    def test_skips_binary_ignored_and_symlinks(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "README.md").write_text("Welcome\n", encoding="utf-8")
            (root / "LICENSE").write_text("MIT License\n", encoding="utf-8")
            (root / "blob.bin").write_bytes(b"\x00TODO  ")
            (root / "skip.log").write_text("TODO\n", encoding="utf-8")
            (root / "node_modules").mkdir()
            (root / "node_modules" / "a.js").write_text("TODO\n", encoding="utf-8")
            # Symbolic links should not point the scanner outside the root.
            try:
                (root / "link").symlink_to(root / "skip.log")
            except (OSError, NotImplementedError):
                pass
            report = audit_repository(root, ignore=("*.log",))
            self.assertEqual(report.findings, ())
            self.assertEqual(report.files_checked, 3)
            self.assertEqual(report.text_files_scanned, 2)

    def test_large_files_are_not_text_scanned(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "big.txt").write_text("TODO " + "x" * 1200, encoding="utf-8")
            report = audit_repository(root, max_file_kb=1)
            self.assertIn("large_file", {f.rule for f in report.findings})
            self.assertEqual(0, report.text_files_scanned)
            self.assertNotIn("developer_note", {f.rule for f in report.findings})

    def test_json_cli_and_strict_exit(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "README.md").write_text("Hello", encoding="utf-8")
            (root / "LICENSE").write_text("MIT", encoding="utf-8")
            output = StringIO()
            with redirect_stdout(output):
                status = main([str(root), "--json", "--strict"])
            self.assertEqual(status, 0)
            data = json.loads(output.getvalue())
            self.assertEqual(data["finding_count"], 0)
            (root / "notes.py").write_text("# FIXME\n", encoding="utf-8")
            with redirect_stdout(StringIO()):
                status = main([str(root), "--strict"])
            self.assertEqual(status, 1)

    def test_missing_directory_and_threshold(self):
        with TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                audit_repository(Path(folder) / "missing")
            with self.assertRaises(ValueError):
                audit_repository(folder, max_file_kb=0)


if __name__ == "__main__":
    unittest.main()
