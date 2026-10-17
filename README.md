# TARAW — Tiny Automated Repository Audit Workflow

A small, open-source Python command-line tool for checking basic repository
hygiene. TARAW makes it easier to notice unfinished developer notes, whitespace
issues, unexpectedly large files, and missing project documentation.

This is an **early-stage starter project**. It has no runtime dependencies and
is intended to be easy to understand, extend, and contribute to.

## Features

- Finds `TODO` and `FIXME` markers in readable UTF-8 text files
- Detects trailing spaces and tabs
- Reports files larger than a configurable threshold
- Warns when the repository root lacks a README or license
- Exports easy-to-process JSON for other tools
- Offers `--strict` mode for scripts and CI
- Skips common dependency/build folders, binary files, and symbolic links

TARAW is **not** a vulnerability scanner, formatter, or full static analyzer.
It does not currently use `.gitignore` rules; it has its own default exclusions
and a repeatable `--ignore` option.

## Requirements

Python 3.10 or newer.

## Install

Download or clone the repository, open a terminal in the project directory,
and run:

```bash
python -m pip install -e .
```

This registers the `taraw` command. You can also use `python -m taraw` after
installation.

## Examples

```bash
# Scan the current folder and print a readable report
taraw .

# Scan another folder and produce JSON
taraw path/to/your/project --json

# Use a smaller file threshold, ignore lock files, and fail on findings
taraw . --max-kb 128 --ignore '*.lock' --strict

# Show help
taraw --help
```

Sample output:

```text
TARAW audit: /path/to/project
Checked 3 files (3 readable text files)
Found 2 issue(s):
- . [missing_license] Add an open-source LICENSE file.
- app.py:4 [developer_note] Review TODO comment.
```

The text output is illustrative, not a result from this repo.

## Rules

| Rule | Meaning |
| ---- | ------- |
| `developer_note` | A line contains the whole word TODO or FIXME |
| `trailing_whitespace` | A line ends in a space or tab |
| `large_file` | A file exceeds `--max-kb` (default 512 KiB) |
| `missing_readme` | No recognized README at the root |
| `missing_license` | No recognized LICENSE at the root |
| `unreadable_file` | TARAW could not access file metadata |

For safety and speed, oversized files are reported but not opened. Other
unreadable or non-UTF-8 files and binary files are skipped during text checks.

## Running tests

```bash
python -m unittest discover -s tests -v
```

A GitHub Actions workflow runs the same tests on supported Python versions.

## Project status and roadmap

**Status:** Version 0.1.0, initial community-ready prototype.

Possible future improvements (not yet implemented):
- Optional `.gitignore` support
- Configuration file for projects with many exclusions
- Rule-specific switches and exit codes
- Faster scanning of very large repositories
- Better reporting and editor integrations

## Contributing

Bug reports, documentation improvements, test cases, and focused new features
are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) for instructions.

## License

Released under the [MIT License](LICENSE).
