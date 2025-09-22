"""Command line interface for the task manager."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Iterable, List, Optional

from .manager import TaskManager
from .storage import TaskStorage
from .models import Task

DEFAULT_DB_PATH = Path.home() / ".simple_task_manager" / "tasks.json"


def create_storage(path: Optional[str] = None) -> TaskStorage:
    """Create storage instance using the configured path or default."""
    if path is None:
        path = os.environ.get("TASK_MANAGER_DB", str(DEFAULT_DB_PATH))
    return TaskStorage(Path(path))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="シンプルなタスク管理ツール")
    parser.add_argument(
        "--database",
        "-d",
        dest="database",
        help="タスクを保存する JSON ファイルのパス (既定: ~/.simple_task_manager/tasks.json)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="タスクを追加")
    add_parser.add_argument("title", help="タスクのタイトル")
    add_parser.add_argument("--description", "-m", default="", help="詳細メモ")
    add_parser.add_argument("--due-date", "-t", dest="due_date", help="期限 (YYYY-MM-DD)")
    add_parser.add_argument(
        "--priority",
        "-p",
        choices=TaskManager.PRIORITY_LEVELS,
        default="normal",
        help="優先度 (low / normal / high)",
    )

    list_parser = subparsers.add_parser("list", help="タスクを一覧表示")
    list_parser.add_argument(
        "--status",
        choices=["all", "pending", "completed"],
        default="all",
        help="表示対象 (all: すべて, pending: 未完了, completed: 完了済み)",
    )
    list_parser.add_argument(
        "--detailed",
        action="store_true",
        help="詳細情報 (メモや作成日時) を表示",
    )

    complete_parser = subparsers.add_parser("complete", help="タスクを完了にする")
    complete_parser.add_argument("task_id", type=int, help="対象のタスク ID")
    complete_parser.add_argument(
        "--undo",
        action="store_true",
        help="完了状態を解除する",
    )

    update_parser = subparsers.add_parser("update", help="タスク情報を更新")
    update_parser.add_argument("task_id", type=int, help="対象のタスク ID")
    update_parser.add_argument("--title")
    update_parser.add_argument("--description")
    update_parser.add_argument("--due-date", dest="due_date")
    update_parser.add_argument("--priority", choices=TaskManager.PRIORITY_LEVELS)
    update_parser.add_argument(
        "--status",
        choices=["pending", "completed"],
        help="タスクの状態",
    )

    delete_parser = subparsers.add_parser("delete", help="タスクを削除")
    delete_parser.add_argument("task_id", type=int, help="対象のタスク ID")

    return parser


def format_tasks(tasks: Iterable[Task]) -> str:
    """Render tasks as a simple table."""
    rows: List[List[str]] = []
    for task in tasks:
        rows.append(
            [
                str(task.id),
                "✔" if task.completed else " ",
                task.title,
                task.due_date or "-",
                task.priority,
            ]
        )
    headers = ["ID", "完", "タイトル", "期限", "優先度"]
    table = _render_table(headers, rows)
    return table


def format_detailed(task: Task) -> str:
    lines = [
        f"[{task.id}] {task.title}",
        f"  状態: {'完了' if task.completed else '進行中'}",
        f"  優先度: {task.priority}",
        f"  期限: {task.due_date or '未設定'}",
    ]
    if task.description:
        lines.append(f"  メモ: {task.description}")
    lines.append(f"  作成日時: {task.created_at}")
    lines.append(f"  更新日時: {task.updated_at}")
    return "\n".join(lines)


def _render_table(headers: List[str], rows: List[List[str]]) -> str:
    if not rows:
        return "登録済みのタスクはありません。"
    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))
    header_line = " | ".join(header.ljust(widths[i]) for i, header in enumerate(headers))
    separator = "-+-".join("-" * width for width in widths)
    row_lines = [
        " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)) for row in rows
    ]
    return "\n".join([header_line, separator, *row_lines])


def command_add(manager: TaskManager, args: argparse.Namespace) -> None:
    task = manager.add_task(
        title=args.title,
        description=args.description,
        due_date=args.due_date,
        priority=args.priority,
    )
    print(f"タスクを追加しました (ID: {task.id})")


def command_list(manager: TaskManager, args: argparse.Namespace) -> None:
    status = None if args.status == "all" else args.status
    tasks = manager.list_tasks(status=status)
    if args.detailed:
        if not tasks:
            print("登録済みのタスクはありません。")
            return
        print("\n\n".join(format_detailed(task) for task in tasks))
    else:
        print(format_tasks(tasks))


def command_complete(manager: TaskManager, args: argparse.Namespace) -> None:
    completed = not args.undo
    task = manager.complete_task(args.task_id, completed=completed)
    state = "完了" if completed else "未完了"
    print(f"タスク {task.id} を{state}に設定しました。")


def command_update(manager: TaskManager, args: argparse.Namespace) -> None:
    completed: Optional[bool]
    if args.status is None:
        completed = None
    else:
        completed = args.status == "completed"
    task = manager.update_task(
        args.task_id,
        title=args.title,
        description=args.description,
        due_date=args.due_date,
        priority=args.priority,
        completed=completed,
    )
    print(f"タスク {task.id} を更新しました。")


def command_delete(manager: TaskManager, args: argparse.Namespace) -> None:
    manager.delete_task(args.task_id)
    print(f"タスク {args.task_id} を削除しました。")


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    storage = create_storage(args.database)
    manager = TaskManager(storage)

    commands = {
        "add": command_add,
        "list": command_list,
        "complete": command_complete,
        "update": command_update,
        "delete": command_delete,
    }

    command = commands.get(args.command)
    if command is None:
        parser.error("不明なコマンドです。")
        return 2

    try:
        command(manager, args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
