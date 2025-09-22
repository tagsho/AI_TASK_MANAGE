"""File based storage backend for task data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List

from .models import Task


class TaskStorage:
    """Persist tasks to a JSON file on disk."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load_tasks(self) -> List[Task]:
        """Load all stored tasks."""
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as handle:
            raw_tasks = json.load(handle)
        return [Task.from_dict(item) for item in raw_tasks]

    def save_tasks(self, tasks: Iterable[Task]) -> None:
        """Persist the given tasks list."""
        serialisable = [task.to_dict() for task in tasks]
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(serialisable, handle, ensure_ascii=False, indent=2)
