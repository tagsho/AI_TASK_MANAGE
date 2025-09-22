# Simple Task Manager

A lightweight command-line application for organising tasks. Tasks can include optional descriptions and due dates and are stored in a JSON file so they persist between runs.

## Features

- Add new tasks with optional description and due date
- List all tasks or filter by completion status
- Update titles, descriptions, completion status, and due dates
- Remove tasks that are no longer needed
- Persist tasks to a JSON file for later sessions

## Getting Started

### Prerequisites

- Python 3.10 or newer

### Installation

No third-party dependencies are required. You may create a virtual environment if desired, but the standard library is sufficient.

### Usage

Every command accepts an optional `--storage` argument that sets the path of the JSON file used for persistence. When omitted, `tasks.json` in the current directory is used.

Create a task:

```bash
python -m app.main add "Write report" --description "Summarise Q2 results" --due 2025-06-30
```

List tasks:

```bash
python -m app.main list --status pending
```

Mark a task as complete and remove the due date:

```bash
python -m app.main update 1 --completed true --clear-due
```

Delete a task:

```bash
python -m app.main delete 1
```

### Running Tests

```bash
pytest
```

## Project Structure

```
app/
├── __init__.py
├── main.py          # Command-line interface
├── models.py        # Dataclass representing a task
└── repository.py    # Task repository with optional JSON persistence

requirements.txt     # Documented dependencies (none required)
tests/
└── test_app.py      # Unit tests for the repository and CLI
```
