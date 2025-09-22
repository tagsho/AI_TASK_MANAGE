"""Business logic for the task manager."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Optional

from .models import Task
from .storage import TaskStorage


class TaskManager:
    """High level API used by the CLI to manage tasks."""

    PRIORITY_LEVELS = ("low", "normal", "high")

    def __init__(self, storage: TaskStorage) -> None:
        self.storage = storage

    def _validate_priority(self, priority: str) -> str:
        if priority not in self.PRIORITY_LEVELS:
            raise ValueError(
                f"優先度は {', '.join(self.PRIORITY_LEVELS)} のいずれかを指定してください。"
            )
        return priority

    def _normalise_due_date(self, due_date: Optional[str]) -> Optional[str]:
        if due_date in (None, ""):
            return None
        try:
            parsed = datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("期限は YYYY-MM-DD 形式で指定してください。") from exc
        return parsed.date().isoformat()

    def _load(self) -> List[Task]:
        return self.storage.load_tasks()

    def _save(self, tasks: Iterable[Task]) -> None:
        self.storage.save_tasks(tasks)

    def add_task(
        self,
        *,
        title: str,
        description: str = "",
        due_date: Optional[str] = None,
        priority: str = "normal",
    ) -> Task:
        tasks = self._load()
        due = self._normalise_due_date(due_date)
        priority_value = self._validate_priority(priority)
        next_id = max((task.id for task in tasks), default=0) + 1
        new_task = Task(
            id=next_id,
            title=title,
            description=description,
            due_date=due,
            priority=priority_value,
        )
        tasks.append(new_task)
        self._save(tasks)
        return new_task

    def list_tasks(self, *, status: Optional[str] = None) -> List[Task]:
        tasks = self._load()
        if status == "pending":
            tasks = [task for task in tasks if not task.completed]
        elif status == "completed":
            tasks = [task for task in tasks if task.completed]
        return sorted(
            tasks,
            key=lambda task: (
                task.completed,
                task.due_date or "9999-12-31",
                task.id,
            ),
        )

    def _find_task(self, task_id: int, tasks: List[Task]) -> Task:
        for task in tasks:
            if task.id == task_id:
                return task
        raise ValueError(f"ID {task_id} のタスクが見つかりません。")

    def update_task(
        self,
        task_id: int,
        *,
        title: Optional[str] = None,
        description: Optional[str] = None,
        due_date: Optional[Optional[str]] = None,
        priority: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> Task:
        tasks = self._load()
        task = self._find_task(task_id, tasks)
        if priority is not None:
            priority = self._validate_priority(priority)
        if due_date is not None:
            due_date = self._normalise_due_date(due_date)
        task.apply_updates(
            title=title,
            description=description,
            due_date=due_date,
            priority=priority,
            completed=completed,
        )
        self._save(tasks)
        return task

    def complete_task(self, task_id: int, *, completed: bool = True) -> Task:
        return self.update_task(task_id, completed=completed)

    def delete_task(self, task_id: int) -> None:
        tasks = self._load()
        task = self._find_task(task_id, tasks)
        tasks.remove(task)
        self._save(tasks)
