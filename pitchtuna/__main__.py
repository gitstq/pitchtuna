"""Module entry point so ``python -m pitchtuna`` works without installation."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
