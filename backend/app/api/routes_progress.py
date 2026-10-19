"""API routes for tracking and managing user progress."""

from fastapi import APIRouter
from pydantic import BaseModel

from backend.app.storage import ProgressReport, storage

router = APIRouter(prefix="/api", tags=["Progress"])


class ResetResponse(BaseModel):
    success: bool
    message: str


@router.get("/progress", response_model=ProgressReport)
def get_progress() -> ProgressReport:
    """Retrieve overall user progress, completed task count and percentage."""
    return storage.get_progress_report()


@router.post("/progress/reset", response_model=ResetResponse)
def reset_progress() -> ResetResponse:
    """Reset user progress and clear saved solutions."""
    storage.reset_progress()
    return ResetResponse(
        success=True,
        message="Прогресс успешно сброшен",
    )
