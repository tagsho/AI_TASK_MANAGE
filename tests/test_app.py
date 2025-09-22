from datetime import date, timedelta
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.main import main
from app.repository import TaskRepository


@pytest.fixture
def repository(tmp_path: Path) -> TaskRepository:
    storage = tmp_path / "tasks.json"
    return TaskRepository(storage_path=storage)


def test_create_and_get_task(repository: TaskRepository):
    due = date.today() + timedelta(days=7)
    task = repository.create_task("Write documentation", description="Update README", due_date=due)

    fetched = repository.get_task(task.id)
    assert fetched is not None
    assert fetched.title == "Write documentation"
    assert fetched.description == "Update README"
    assert fetched.due_date == due
    assert fetched.completed is False


def test_list_and_filter_tasks(repository: TaskRepository):
    first = repository.create_task("Task A")
    second = repository.create_task("Task B")
    repository.update_task(second.id, completed=True)

    all_tasks = list(repository.list_tasks())
    assert len(all_tasks) == 2

    completed_tasks = list(repository.list_tasks(completed=True))
    assert [task.id for task in completed_tasks] == [second.id]

    pending_tasks = list(repository.list_tasks(completed=False))
    assert [task.id for task in pending_tasks] == [first.id]


def test_update_and_delete_task(repository: TaskRepository):
    task = repository.create_task("Temporary", description="To be updated")

    updated = repository.update_task(
        task.id,
        title="Updated title",
        description="New description",
        completed=True,
    )
    assert updated.title == "Updated title"
    assert updated.description == "New description"
    assert updated.completed is True

    repository.update_task(task.id, due_date=date(2025, 1, 1))
    repository.update_task(task.id, due_date=None)
    assert repository.get_task(task.id).due_date is None

    assert repository.delete_task(task.id) is True
    assert repository.get_task(task.id) is None
    assert repository.delete_task(task.id) is False


def test_validation_and_error_handling(repository: TaskRepository):
    with pytest.raises(ValueError):
        repository.create_task("   ")

    task = repository.create_task("Valid title")
    with pytest.raises(ValueError):
        repository.update_task(task.id, title="")

    with pytest.raises(KeyError):
        repository.update_task(9999, title="Unknown")


def test_persistence_between_sessions(tmp_path: Path):
    storage = tmp_path / "tasks.json"
    repo_a = TaskRepository(storage_path=storage)
    repo_a.create_task("Persistent task", due_date=date(2030, 1, 1))

    repo_b = TaskRepository(storage_path=storage)
    tasks = list(repo_b.list_tasks())
    assert len(tasks) == 1
    assert tasks[0].title == "Persistent task"
    assert tasks[0].due_date == date(2030, 1, 1)


def test_cli_flow(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    storage = tmp_path / "cli_tasks.json"

    # Listing before creation shows no tasks.
    exit_code = main(["--storage", str(storage), "list"])
    assert exit_code == 0
    output = capsys.readouterr().out
    assert "No tasks found" in output

    exit_code = main(
        [
            "--storage",
            str(storage),
            "add",
            "Buy milk",
            "--description",
            "From the local store",
            "--due",
            "2025-05-01",
        ]
    )
    assert exit_code == 0
    capsys.readouterr()

    exit_code = main(["--storage", str(storage), "list", "--status", "pending"])
    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Buy milk" in output
    assert "✗" in output

    # Mark as completed
    exit_code = main(["--storage", str(storage), "update", "1", "--completed", "true"])
    assert exit_code == 0
    capsys.readouterr()

    exit_code = main(["--storage", str(storage), "list", "--status", "completed"])
    assert exit_code == 0
    output = capsys.readouterr().out
    assert "✓" in output

    exit_code = main(["--storage", str(storage), "delete", "1"])
    assert exit_code == 0

    exit_code = main(["--storage", str(storage), "delete", "999"])
    assert exit_code == 1
    output = capsys.readouterr().out
    assert "not found" in output.lower()
