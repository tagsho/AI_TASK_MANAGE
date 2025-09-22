"""Data models for the task manager application."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional

TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S"


def current_timestamp() -> str:
    """Return the current UTC timestamp formatted for storage."""
    return datetime.now(timezone.utc).strftime(TIMESTAMP_FORMAT)


@dataclass
class Task:
    """Representation of a single task item."""

    id: int
    title: str
    description: str = ""
    due_date: Optional[str] = None
    priority: str = "normal"
    completed: bool = False
    created_at: str = field(default_factory=current_timestamp)
    updated_at: str = field(default_factory=current_timestamp)

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON serialisable representation of the task."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Create a task instance from stored JSON data."""
        defaults = {
            "description": "",
            "due_date": None,
            "priority": "normal",
            "completed": False,
            "created_at": current_timestamp(),
            "updated_at": current_timestamp(),
        }
        merged: Dict[str, Any] = {**defaults, **data}
        return cls(**merged)

    def mark_completed(self, completed: bool = True) -> None:
        """Toggle the completion state and update the timestamp."""
        self.completed = completed
        self.updated_at = current_timestamp()

    def apply_updates(
        self,
        *,
        title: Optional[str] = None,
        description: Optional[str] = None,
        due_date: Optional[Optional[str]] = None,
        priority: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> None:
        """Update editable fields and refresh the ``updated_at`` timestamp."""

        if title is not None:
            self.title = title
        if description is not None:
            self.description = description
        if due_date is not None:
            self.due_date = due_date
        if priority is not None:
            self.priority = priority
        if completed is not None:
            self.completed = completed
        self.updated_at = current_timestamp()
