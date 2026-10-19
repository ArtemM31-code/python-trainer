"""Integration tests for all FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.storage import storage


@pytest.fixture
def client():
    # Reset progress before tests
    storage.reset_progress()
    with TestClient(app) as test_client:
        yield test_client
    storage.reset_progress()


def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "python-trainer-backend" in data["service"]


def test_get_topics(client):
    response = client.get("/api/topics")
    assert response.status_code == 200
    topics = response.json()
    assert isinstance(topics, list)
    assert len(topics) >= 1
    first = topics[0]
    assert "id" in first
    assert "title" in first
    assert "tasks_count" in first
    assert "completed_count" in first


def test_get_tasks(client):
    response = client.get("/api/tasks")
    assert response.status_code == 200
    tasks = response.json()
    assert isinstance(tasks, list)
    assert len(tasks) >= 1
    assert "id" in tasks[0]
    assert "topic_id" in tasks[0]
    assert "title" in tasks[0]
    assert "difficulty" in tasks[0]
    assert "completed" in tasks[0]


def test_get_tasks_filter_by_topic(client):
    response = client.get("/api/tasks?topic_id=basics")
    assert response.status_code == 200
    tasks = response.json()
    assert isinstance(tasks, list)
    assert len(tasks) > 0
    for t in tasks:
        assert t["topic_id"] == "basics"


def test_get_task_details(client):
    response = client.get("/api/tasks/basics-01-format-greeting")
    assert response.status_code == 200
    detail = response.json()
    assert detail["id"] == "basics-01-format-greeting"
    assert detail["topic_id"] == "basics"
    assert "theory" in detail
    assert "instructions" in detail
    assert "starter_code" in detail
    assert detail["tests_count"] > 0
    assert detail["completed"] is False


def test_get_task_not_found(client):
    response = client.get("/api/tasks/non-existent-task-id-12345")
    assert response.status_code == 404


def test_run_code(client):
    payload = {"code": "x = 40\ny = 2\nprint(f'Answer: {x + y}')"}
    response = client.post("/api/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Answer: 42" in data["stdout"]
    assert data["stderr"] == ""
    assert data["exit_code"] == 0
    assert data["execution_time_ms"] > 0


def test_run_code_syntax_error(client):
    payload = {"code": "def oops(\nprint('bad')"}
    response = client.post("/api/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "SyntaxError" in data["stderr"]


def test_run_code_timeout(client):
    payload = {"code": "while True:\n    pass"}
    response = client.post("/api/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["exit_code"] == -1
    assert "Превышено максимальное время" in data["stderr"]


def test_test_task_solution(client):
    task_id = "basics-01-format-greeting"
    solution = (
        "def format_greeting(name: str, age: int) -> str:\n"
        "    return f'Привет, {name.strip().capitalize()}! Тебе {age} лет.'\n"
    )
    payload = {"code": solution}
    response = client.post(f"/api/test/{task_id}", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["passed"] is True
    assert data["score"] == 100
    assert data["passed_tests"] == data["total_tests"]

    # Check progress update
    prog_resp = client.get("/api/progress")
    assert prog_resp.status_code == 200
    prog_data = prog_resp.json()
    assert task_id in prog_data["completed_ids"]
    assert prog_data["completed_tasks"] >= 1

    # Check task detail now returns completed=True and user_solution
    task_resp = client.get(f"/api/tasks/{task_id}")
    assert task_resp.status_code == 200
    task_data = task_resp.json()
    assert task_data["completed"] is True
    assert task_data["user_solution"] == solution


def test_progress_reset(client):
    # Complete a task first
    task_id = "basics-01-format-greeting"
    solution = (
        "def format_greeting(name: str, age: int) -> str:\n"
        "    return f'Привет, {name.strip().capitalize()}! Тебе {age} лет.'\n"
    )
    client.post(f"/api/test/{task_id}", json={"code": solution})

    # Reset progress
    reset_resp = client.post("/api/progress/reset")
    assert reset_resp.status_code == 200
    assert reset_resp.json()["success"] is True

    # Verify progress is 0
    prog_resp = client.get("/api/progress")
    assert prog_resp.status_code == 200
    prog_data = prog_resp.json()
    assert prog_data["completed_tasks"] == 0
    assert len(prog_data["completed_ids"]) == 0
    assert prog_data["percentage"] == 0.0


def test_root_index_page(client):
    response = client.get("/")
    assert response.status_code == 200
