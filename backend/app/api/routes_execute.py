"""API routes for code execution and automated task testing."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.runner import ExecutionResult, TestSuiteResult, execute_code, run_tests
from backend.app.storage import storage

router = APIRouter(prefix="/api", tags=["Execution"])


class CodeRunRequest(BaseModel):
    code: str = Field(..., description="Python code string to execute")


class CodeTestRequest(BaseModel):
    code: str = Field(..., description="Python code string to evaluate against task test cases")


@router.post("/run", response_model=ExecutionResult)
def run_code_endpoint(req: CodeRunRequest) -> ExecutionResult:
    """Execute arbitrary Python code in an isolated subprocess with timeout."""
    return execute_code(req.code)


@router.post("/test/{task_id}", response_model=TestSuiteResult)
def test_task_endpoint(task_id: str, req: CodeTestRequest) -> TestSuiteResult:
    """
    Test user code against the test cases defined for task_id.
    Persists user code and marks task completed upon passing.
    """
    task = storage.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Задание '{task_id}' не найдено.")

    # Run tests against task's test cases
    results = run_tests(code=req.code, test_cases=task.test_cases)

    # Persist code and record completion status
    all_completed = storage.record_submission(
        task_id=task_id,
        code=req.code,
        passed=results.passed,
    )
    results.all_completed = all_completed

    return results
