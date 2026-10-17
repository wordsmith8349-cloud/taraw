"""Command line interface for TARAW."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from . import __version__
from .audit import audit_repository


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="taraw",
        description="Run lightweight code-hygiene checks on a repository.",
    )
    parser.add_argument("path", nargs="?", default=".", help="Directory to audit (default: current directory).")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON results.")
    parser.add_argument("--strict", action="store_true", help="Exit 1 if any findings are present (useful in CI).")
    parser.add_argument("--max-kb", type=int, default=512, metavar="N", help="Report files larger than N KiB (default: 512).")
    parser.add_argument("--ignore", action="append", default=[], metavar="GLOB", help="Ignore matching paths (repeatable); e.g. --ignore '*.lock'.")
    parser.add_argument("--version", action="version", version=f"TARAW {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.max_kb < 1:
        parser.error("--max-kb must be a positive integer")
    try:
        report = audit_repository(Path(args.path), max_file_kb=args.max_kb, ignore=tuple(args.ignore))
    except ValueError as exc:
        parser.error(str(exc))

    if args.json:
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(f"TARAW audit: {report.root}")
        print(f"Checked {report.files_checked} files ({report.text_files_scanned} readable text files)")
        if not report.findings:
            print("No findings. Nice work!")
        else:
            print(f"Found {len(report.findings)} issue(s):")
            for finding in report.findings:
                location = f"{finding.path}:{finding.line}" if finding.line else finding.path
                print(f"- {location} [{finding.rule}] {finding.message}")
    return 1 if args.strict and report.findings else 0


if __name__ == "__main__":
    sys.exit(main())
