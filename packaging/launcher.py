"""PyInstaller entry point (absolute imports, no relative-import ambiguity)."""

from pitchtuna.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
