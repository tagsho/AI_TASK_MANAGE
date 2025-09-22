"""Tests for the task manager domain logic."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from task_manager.manager import TaskManager
from task_manager.storage import TaskStorage


@pytest.fixture()
def manager(tmp_path: Path) -> TaskManager:
    storage_path = tmp_path / "tasks.json"
    storage = TaskStorage(storage_path)
    return TaskManager(storage)


def read_raw_tasks(path: Path) -> list[dict[str, object]]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_add_and_list_tasks(manager: TaskManager, tmp_path: Path) -> None:
    manager.add_task(title="書類作成", description="請求書のドラフト", due_date="2024-12-01")
    manager.add_task(title="買い物", priority="high")
    all_tasks = manager.list_tasks()
    assert len(all_tasks) == 2
    assert all_tasks[0].title == "書類作成"
    assert all_tasks[0].due_date == "2024-12-01"
    pending_tasks = manager.list_tasks(status="pending")
    assert len(pending_tasks) == 2


def test_complete_task(manager: TaskManager) -> None:
    task = manager.add_task(title="散歩")
    assert not task.completed
    manager.complete_task(task.id)
    stored = manager.list_tasks()
    assert stored[0].completed
    manager.complete_task(task.id, completed=False)
    assert not manager.list_tasks()[0].completed


def test_update_task(manager: TaskManager) -> None:
    task = manager.add_task(title="洗濯", due_date="2024-01-10")
    updated = manager.update_task(
        task.id,
        title="洗濯物を畳む",
        description="Tシャツとタオル",
        due_date="2024-01-12",
        priority="high",
        completed=True,
    )
    assert updated.title == "洗濯物を畳む"
    assert updated.description == "Tシャツとタオル"
    assert updated.due_date == "2024-01-12"
    assert updated.priority == "high"
    assert updated.completed is True


def test_delete_task(manager: TaskManager, tmp_path: Path) -> None:
    task1 = manager.add_task(title="メール送信")
    task2 = manager.add_task(title="資料レビュー")
    manager.delete_task(task1.id)
    remaining = manager.list_tasks()
    assert len(remaining) == 1
    assert remaining[0].id == task2.id


def test_invalid_priority(manager: TaskManager) -> None:
    with pytest.raises(ValueError):
        manager.add_task(title="無効な優先度", priority="urgent")


def test_invalid_due_date(manager: TaskManager) -> None:
    with pytest.raises(ValueError):
        manager.add_task(title="日付", due_date="2024/12/01")


def test_storage_persists_data(tmp_path: Path) -> None:
    storage_path = tmp_path / "tasks.json"
    manager = TaskManager(TaskStorage(storage_path))
    manager.add_task(title="掃除", description="玄関")
    raw = read_raw_tasks(storage_path)
    assert raw[0]["title"] == "掃除"
    assert raw[0]["description"] == "玄関"
