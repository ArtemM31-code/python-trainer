# Python Interactive Trainer - System Architecture & Specifications

## Overview
An interactive Python Learning Platform & Code Runner built with FastAPI backend and a modern browser-based IDE frontend (Monaco Editor / VS Code engine via CDN). The user selects a topic, reads theory/task description, writes code in the editor, runs it with live terminal output, and submits it for automated test validation.

---

## Directory Layout
```
python-trainer/
├── ARCHITECTURE.md
├── README.md
├── requirements.txt
├── run.py                 # Main entrypoint: starts uvicorn with auto-reload & opens browser
├── .gitignore
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py        # FastAPI app, static file serving, CORS
│   │   ├── config.py      # App settings & paths
│   │   ├── runner.py      # Sandboxed code execution & test validation engine
│   │   ├── storage.py     # Tasks registry and user progress tracking (JSON/SQLite)
│   │   └── api/
│   │       ├── __init__.py
│   │       ├── routes_tasks.py    # GET /api/topics, GET /api/tasks, GET /api/tasks/{id}
│   │       ├── routes_execute.py  # POST /api/run, POST /api/test/{task_id}
│   │       └── routes_progress.py # GET /api/progress, POST /api/progress/reset
│   └── tests/
│       ├── __init__.py
│       ├── test_runner.py
│       └── test_api.py
├── content/
│   └── tasks/
│       ├── 01_basics.json
│       ├── 02_data_structures.json
│       ├── 03_functions.json
│       ├── 04_args_kwargs.json
│       ├── 05_closures_legb.json
│       ├── 06_decorators.json
│       ├── 07_exceptions.json
│       └── 08_oop.json
└── frontend/
    ├── index.html         # Responsive Split-Pane Web IDE
    ├── css/
    │   └── style.css      # Dark theme, modern UI, typography, badges, progress bar
    └── js/
        ├── app.js         # Core application logic, API client, state
        └── editor.js      # Monaco Editor setup & keyboard shortcuts (Ctrl+Enter to run)
```

---

## API Specification

### 1. Topics & Tasks
- `GET /api/topics`
  Response:
  ```json
  [
    {
      "id": "functions",
      "title": "Функции в Python",
      "description": "Определение функций, параметры, возвращаемые значения",
      "tasks_count": 4,
      "completed_count": 1
    }
  ]
  ```

- `GET /api/tasks` (optional query: `?topic_id=functions`)
  Response: array of task summaries:
  ```json
  [
    {
      "id": "func-01-greeting",
      "topic_id": "functions",
      "title": "Функция приветствия",
      "difficulty": "easy",
      "completed": true
    }
  ]
  ```

- `GET /api/tasks/{task_id}`
  Response: full task details:
  ```json
  {
    "id": "func-01-greeting",
    "topic_id": "functions",
    "title": "Функция приветствия",
    "difficulty": "easy",
    "theory": "Markdown text with explanation...",
    "instructions": "Напишите функцию `greet(name)`...",
    "starter_code": "def greet(name: str) -> str:\n    pass\n",
    "hint": "Используйте f-строку `f'Привет, {name}!'`",
    "tests_count": 3,
    "completed": false,
    "user_solution": "def greet(name: str) -> str:\n    return f'Привет, {name}!'"
  }
  ```

### 2. Code Execution & Testing
- `POST /api/run`
  Request:
  ```json
  { "code": "print('Hello world!')" }
  ```
  Response:
  ```json
  {
    "success": true,
    "stdout": "Hello world!\n",
    "stderr": "",
    "execution_time_ms": 25.4,
    "exit_code": 0
  }
  ```

- `POST /api/test/{task_id}`
  Request:
  ```json
  { "code": "def greet(name):\n    return f'Привет, {name}!'" }
  ```
  Response:
  ```json
  {
    "passed": true,
    "score": 100,
    "total_tests": 3,
    "passed_tests": 3,
    "test_results": [
      {
        "test_name": "greet('Алексей')",
        "passed": true,
        "expected": "Привет, Алексей!",
        "actual": "Привет, Алексей!",
        "message": ""
      }
    ],
    "stdout": "",
    "stderr": "",
    "all_completed": false
  }
  ```

### 3. Progress Tracking
- `GET /api/progress`
  Response: `{ "total_tasks": 25, "completed_tasks": 7, "percentage": 28.0, "completed_ids": [...] }`
- `POST /api/progress/reset`
  Response: `{ "success": true, "message": "Прогресс успешно сброшен" }`

---

## Code Execution Security & Isolation
- Runs via a separate Python subprocess with strict timeout (e.g., 4 seconds) to prevent infinite loops (`while True:`).
- Restricts unsafe operations where possible and captures `stdout` / `stderr` cleanly.
- Test runner injects verification assertions and returns structured test outcomes.
