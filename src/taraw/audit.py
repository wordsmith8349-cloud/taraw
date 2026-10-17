"""Deterministic, dependency-free checks for small source repositories.

TARAW is a code-hygiene checker, not a security scanner or static analyzer.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from fnmatch import fnmatch
import os
from pathlib import Path
import re

DEFAULT_IGNORED_DIRS = frozenset(
    {".git", ".hg", ".svn", ".venv", "venv", "node_modules",
     "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache",
     "dist", "build", ".tox", ".idea"}
)
NOTE_PATTERN = re.compile(r"\b(TODO|FIXME)\b", re.IGNORECASE)
README_NAMES = frozenset({"readme", "readme.md", "readme.rst", "readme.txt"})
LICENSE_NAMES = frozenset({"license", "license.md", "license.txt", "licence", "licence.md", "copying"})


@dataclass(frozen=True)
class Finding:
    rule: str
    path: str
    message: str
    line: int | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class AuditReport:
    root: str
    files_checked: int
    text_files_scanned: int
    findings: tuple[Finding, ...]

    def to_dict(self) -> dict:
        return {
            "root": self.root,
            "files_checked": self.files_checked,
            "text_files_scanned": self.text_files_scanned,
            "finding_count": len(self.findings),
            "findings": [finding.to_dict() for finding in self.findings],
        }


def _matches_ignore(relative: Path, patterns: tuple[str, ...]) -> bool:
    """Match the relative Unix-style path or its basename against globs."""
    rel = relative.as_posix()
    return any(fnmatch(rel, pattern) or fnmatch(relative.name, pattern) for pattern in patterns)


def audit_repository(
    root: str | Path,
    *,
    max_file_kb: int = 512,
    ignore: tuple[str, ...] = (),
) -> AuditReport:
    """Audit a directory for basic maintainability checks.

    Skips symbolic links, common generated directories, and non-UTF-8/binary
    files. Files larger than max_file_kb are reported but not read.
    """
    directory = Path(root).expanduser().resolve()
    if not directory.is_dir():
        raise ValueError(f"Not a directory: {directory}")
    if max_file_kb <= 0:
        raise ValueError("max_file_kb must be a positive integer")

    findings: list[Finding] = []
    files_checked = 0
    text_scanned = 0
    top_level = {p.name.lower() for p in directory.iterdir() if p.is_file()}
    if not top_level.intersection(README_NAMES):
        findings.append(Finding("missing_readme", ".", "Add a README to explain the project."))
    if not top_level.intersection(LICENSE_NAMES):
        findings.append(Finding("missing_license", ".", "Add an open-source LICENSE file."))

    for current, dirs, files in os.walk(directory, topdown=True, followlinks=False):
        current_path = Path(current)
        dirs[:] = sorted(
            name for name in dirs
            if name not in DEFAULT_IGNORED_DIRS
            and not (current_path / name).is_symlink()
            and not _matches_ignore((current_path / name).relative_to(directory), ignore)
        )
        for filename in sorted(files):
            item = current_path / filename
            if item.is_symlink():
                continue
            relative = item.relative_to(directory)
            if _matches_ignore(relative, ignore):
                continue
            try:
                byte_count = item.stat().st_size
            except OSError:
                findings.append(Finding("unreadable_file", relative.as_posix(), "Could not inspect this file."))
                continue
            files_checked += 1
            if byte_count > max_file_kb * 1024:
                findings.append(
                    Finding("large_file", relative.as_posix(),
                            f"File is larger than {max_file_kb} KiB ({byte_count} bytes).")
                )
                continue
            try:
                raw = item.read_bytes()
                if b"\x00" in raw:
                    continue
                contents = raw.decode("utf-8")
            except (OSError, UnicodeError):
                # Not all files are text; skip rather than produce misleading flags.
                continue
            text_scanned += 1
            for lineno, line in enumerate(contents.splitlines(), start=1):
                match = NOTE_PATTERN.search(line)
                if match:
                    findings.append(
                        Finding("developer_note", relative.as_posix(),
                                f"Review {match.group(1).upper()} comment.", lineno)
                    )
                if line.endswith((" ", "\t")):
                    findings.append(
                        Finding("trailing_whitespace", relative.as_posix(),
                                "Remove trailing spaces or tabs.", lineno)
                    )

    findings.sort(key=lambda f: (f.path, f.line or 0, f.rule, f.message))
    return AuditReport(str(directory), files_checked, text_scanned, tuple(findings))
