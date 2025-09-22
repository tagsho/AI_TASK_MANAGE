from __future__ import annotations

import argparse
from datetime import date
from typing import Iterable, Optional, Sequence

from .models import Task
from .repository import TaskRepository


def _parse_due_date(value: Optional[str]) -> Optional[date]:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("Due date must use the YYYY-MM-DD format") from exc


def _format_task(task: Task) -> str:
    status = "✓" if task.completed else "✗"
    due = task.due_date.isoformat() if task.due_date else "-"
    description = f" — {task.description}" if task.description else ""
    return f"[{status}] #{task.id} {task.title} (due: {due}){description}"


def _print_tasks(tasks: Iterable[Task]) -> None:
    tasks = list(tasks)
    if not tasks:
        print("No tasks found.")
        return

    for task in tasks:
        print(_format_task(task))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage tasks from the command line.")
    parser.add_argument(
        "--storage",
        default="tasks.json",
        help="Path to the JSON file where tasks are stored (default: %(default)s)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Create a new task")
    add_parser.add_argument("title", help="Title of the task")
    add_parser.add_argument("--description", default="", help="Optional task description")
    add_parser.add_argument("--due", help="Optional due date in YYYY-MM-DD format")

    list_parser = subparsers.add_parser("list", help="List stored tasks")
    list_parser.add_argument(
        "--status",
        choices=["all", "pending", "completed"],
        default="all",
        help="Filter tasks by completion state",
    )

    update_parser = subparsers.add_parser("update", help="Update an existing task")
    update_parser.add_argument("task_id", type=int, help="Identifier of the task to update")
    update_parser.add_argument("--title", help="New title for the task")
    update_parser.add_argument("--description", help="New description for the task")
    update_parser.add_argument("--due", help="New due date in YYYY-MM-DD format")
    update_parser.add_argument("--clear-due", action="store_true", help="Remove the due date")
    update_parser.add_argument(
        "--completed",
        choices=["true", "false"],
        help="Mark the task as completed or pending",
    )

    delete_parser = subparsers.add_parser("delete", help="Delete a task")
    delete_parser.add_argument("task_id", type=int, help="Identifier of the task to delete")

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repository = TaskRepository(storage_path=args.storage)

    try:
        if args.command == "add":
            due_date = _parse_due_date(args.due)
            task = repository.create_task(
                title=args.title,
                description=args.description,
                due_date=due_date,
            )
            print(f"Created task #{task.id}: {task.title}")
            return 0

        if args.command == "list":
            status_map = {"all": None, "pending": False, "completed": True}
            tasks = repository.list_tasks(completed=status_map[args.status])
            _print_tasks(tasks)
            return 0

        if args.command == "update":
            kwargs = {}
            if args.title is not None:
                kwargs["title"] = args.title
            if args.description is not None:
                kwargs["description"] = args.description

            if args.clear_due:
                kwargs["due_date"] = None
            elif args.due is not None:
                kwargs["due_date"] = _parse_due_date(args.due)

            if args.completed is not None:
                kwargs["completed"] = args.completed == "true"

            repository.update_task(args.task_id, **kwargs)
            print(f"Updated task #{args.task_id}")
            return 0

        if args.command == "delete":
            removed = repository.delete_task(args.task_id)
            if not removed:
                print(f"Task #{args.task_id} was not found.")
                return 1
            print(f"Deleted task #{args.task_id}")
            return 0
    except ValueError as exc:
        parser.error(str(exc))
    except KeyError:
        print(f"Task #{getattr(args, 'task_id', 'unknown')} was not found.")
        return 1

    parser.error("Unknown command")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
