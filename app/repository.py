from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from threading import Lock
from typing import Dict, Iterable, Optional

from .models import Task


_UNSET = object()


@dataclass
class TaskRepository:
    """Manage tasks in memory with optional JSON persistence."""

    storage_path: Optional[Path] = None
    _tasks: Dict[int, Task] = field(default_factory=dict, init=False)
    _next_id: int = field(default=1, init=False)
    _lock: Lock = field(default_factory=Lock, init=False)

    def __post_init__(self) -> None:
        if self.storage_path:
            self.storage_path = Path(self.storage_path)
            self._load()

    # ------------------------------------------------------------------
    # CRUD operations
    # ------------------------------------------------------------------
    def list_tasks(self, completed: Optional[bool] = None) -> Iterable[Task]:
        """Return all tasks, optionally filtering by completion state."""

        with self._lock:
            tasks = list(self._tasks.values())

        if completed is None:
            return tasks

        return [task for task in tasks if task.completed is completed]

    def create_task(
        self,
        title: str,
        description: str = "",
        due_date: Optional[date] = None,
    ) -> Task:
        """Create a new task and persist it if persistence is enabled."""

        title = title.strip()
        if not title:
            raise ValueError("title must not be empty")

        with self._lock:
            task = Task(
                id=self._next_id,
                title=title,
                description=description.strip(),
                completed=False,
                due_date=due_date,
            )
            self._tasks[self._next_id] = task
            self._next_id += 1
            self._save_locked()

        return task

    def get_task(self, task_id: int) -> Optional[Task]:
        """Retrieve a single task by its identifier."""

        with self._lock:
            return self._tasks.get(task_id)

    def update_task(
        self,
        task_id: int,
        *,
        title: Optional[str] = None,
        description: Optional[str] = None,
        due_date: object = _UNSET,
        completed: Optional[bool] = None,
    ) -> Task:
        """Update an existing task and persist the change."""

        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                raise KeyError(task_id)

            if title is not None:
                title = title.strip()
                if not title:
                    raise ValueError("title must not be empty")
                task.title = title

            if description is not None:
                task.description = description.strip()

            if due_date is not _UNSET:
                task.due_date = due_date  # type: ignore[assignment]

            if completed is not None:
                task.completed = completed

            self._tasks[task_id] = task
            self._save_locked()
            return task

    def delete_task(self, task_id: int) -> bool:
        """Remove a task from storage and persist if necessary."""

        with self._lock:
            removed = self._tasks.pop(task_id, None) is not None
            if removed:
                self._save_locked()
            return removed

    def reset(self) -> None:
        """Clear all stored tasks and reset the identifier counter."""

        with self._lock:
            self._tasks.clear()
            self._next_id = 1
            self._save_locked()

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def _load(self) -> None:
        if not self.storage_path or not self.storage_path.exists():
            return

        try:
            with self.storage_path.open("r", encoding="utf-8") as handle:
                raw_tasks = json.load(handle)
        except json.JSONDecodeError as exc:
            raise ValueError("Failed to parse task storage file") from exc

        tasks = [Task.from_dict(raw) for raw in raw_tasks]
        self._tasks = {task.id: task for task in tasks}
        self._next_id = (max(self._tasks.keys()) + 1) if self._tasks else 1

    def _save_locked(self) -> None:
        if not self.storage_path:
            return

        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = [task.to_dict() for task in sorted(self._tasks.values(), key=lambda t: t.id)]
        with self.storage_path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
