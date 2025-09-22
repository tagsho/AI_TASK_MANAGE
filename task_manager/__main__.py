"""Entry point for ``python -m task_manager``."""

from .cli import main


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
