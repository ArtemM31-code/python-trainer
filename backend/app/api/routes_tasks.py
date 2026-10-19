"""API routes for topics and tasks."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.app.storage import TaskSummary, TopicSummary, storage

router = APIRouter(prefix="/api", tags=["Tasks"])


class TaskDetailResponse(BaseModel):
    id: str
    topic_id: str
    title: str
    difficulty: str = "easy"
    theory: str = ""
    instructions: str = ""
    starter_code: str = ""
    hint: str = ""
    tests_count: int = 0
    completed: bool = False
    user_solution: Optional[str] = None


@router.get("/topics", response_model=List[TopicSummary])
def list_topics() -> List[TopicSummary]:
    """Retrieve all available topics with completion statistics."""
    return storage.get_topics()


@router.get("/tasks", response_model=List[TaskSummary])
def list_tasks(topic_id: Optional[str] = Query(None, description="Filter tasks by topic ID")) -> List[TaskSummary]:
    """Retrieve list of tasks, optionally filtered by topic."""
    return storage.get_tasks(topic_id=topic_id)


@router.get("/tasks/{task_id}", response_model=TaskDetailResponse)
def get_task_details(task_id: str) -> TaskDetailResponse:
    """Retrieve full details, theory, instructions, and user's saved solution for a task."""
    task = storage.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Задание '{task_id}' не найдено.")

    return TaskDetailResponse(
        id=task.id,
        topic_id=task.topic_id,
        title=task.title,
        difficulty=task.difficulty,
        theory=task.theory,
        instructions=task.instructions,
        starter_code=task.starter_code,
        hint=task.hint,
        tests_count=task.tests_count,
        completed=task.completed,
        user_solution=task.user_solution,
    )
