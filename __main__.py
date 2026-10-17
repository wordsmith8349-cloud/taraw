"""Allow running TARAW with ``python -m taraw``."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
