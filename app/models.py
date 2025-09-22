from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Optional


@dataclass
class Task:
    """Simple representation of a task managed by the application."""

    id: int
    title: str
    description: str = ""
    completed: bool = False
    due_date: Optional[date] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the task to a JSON-friendly dictionary."""

        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "completed": self.completed,
            "due_date": self.due_date.isoformat() if self.due_date else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Deserialize a task from a dictionary produced by :meth:`to_dict`."""

        due_date_value = data.get("due_date")
        parsed_due_date = date.fromisoformat(due_date_value) if due_date_value else None
        return cls(
            id=int(data["id"]),
            title=str(data["title"]),
            description=str(data.get("description", "")),
            completed=bool(data.get("completed", False)),
            due_date=parsed_due_date,
        )
