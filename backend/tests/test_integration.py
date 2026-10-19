"""Integration and QA test suite for Python Interactive Trainer educational content.
Validates tasks schema, content consistency, starter code, test cases, and reference solutions.
"""

import json
import os
import glob
import pytest
from pathlib import Path

# Adjust path to locate content/tasks
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TASKS_DIR = PROJECT_ROOT / "content" / "tasks"

EXPECTED_TOPIC_FILES = [
    "01_basics.json",
    "02_data_structures.json",
    "03_functions.json",
    "04_args_kwargs.json",
    "05_closures_legb.json",
    "06_decorators.json",
    "07_exceptions.json",
    "08_oop.json",
]

REQUIRED_TASK_FIELDS = {
    "id",
    "topic_id",
    "topic_title",
    "title",
    "difficulty",
    "theory",
    "instructions",
    "starter_code",
    "hint",
    "test_cases",
}

VALID_DIFFICULTIES = {"easy", "medium", "hard"}


def load_all_tasks() -> list[dict]:
    """Helper to load all tasks from JSON files."""
    all_tasks = []
    for file_name in EXPECTED_TOPIC_FILES:
        file_path = TASKS_DIR / file_name
        assert file_path.exists(), f"Task file {file_name} does not exist at {file_path}"
        with open(file_path, "r", encoding="utf-8") as f:
            tasks = json.load(f)
            assert isinstance(tasks, list), f"Expected list of tasks in {file_name}"
            for task in tasks:
                task["_source_file"] = file_name
            all_tasks.extend(tasks)
    return all_tasks


class TestTasksContentSchema:
    """Test suite ensuring all task JSON files conform strictly to the platform schema."""

    def test_all_expected_files_exist(self):
        """Verify that all 8 modular JSON topic files exist in content/tasks/."""
        existing_files = {p.name for p in TASKS_DIR.glob("*.json")}
        for expected in EXPECTED_TOPIC_FILES:
            assert expected in existing_files, f"Missing required topic file: {expected}"

    def test_tasks_schema_and_fields(self):
        """Verify that every task has all required fields with appropriate non-empty types."""
        tasks = load_all_tasks()
        assert len(tasks) >= 24, f"Expected at least 24 tasks across 8 topics, got {len(tasks)}"

        for task in tasks:
            task_id = task.get("id", "<missing id>")
            source = task.get("_source_file", "<unknown>")

            # Check presence of all required fields
            missing = REQUIRED_TASK_FIELDS - set(task.keys())
            assert not missing, f"Task '{task_id}' in {source} is missing fields: {missing}"

            # Check field types and non-emptiness
            assert isinstance(task["id"], str) and task["id"].strip(), f"Invalid 'id' in {task_id}"
            assert isinstance(task["topic_id"], str) and task["topic_id"].strip(), f"Invalid 'topic_id' in {task_id}"
            assert isinstance(task["topic_title"], str) and task["topic_title"].strip(), f"Invalid 'topic_title' in {task_id}"
            assert isinstance(task["title"], str) and task["title"].strip(), f"Invalid 'title' in {task_id}"
            assert task["difficulty"] in VALID_DIFFICULTIES, f"Invalid difficulty '{task['difficulty']}' in {task_id}"
            assert isinstance(task["theory"], str) and len(task["theory"].strip()) >= 20, f"Theory too short in {task_id}"
            assert isinstance(task["instructions"], str) and len(task["instructions"].strip()) >= 15, f"Instructions too short in {task_id}"
            assert isinstance(task["starter_code"], str) and task["starter_code"].strip(), f"Starter code empty in {task_id}"
            assert isinstance(task["hint"], str) and task["hint"].strip(), f"Hint empty in {task_id}"

            # Check test_cases structure
            test_cases = task["test_cases"]
            assert isinstance(test_cases, list) and len(test_cases) >= 2, f"Task {task_id} must have >= 2 test cases"
            for idx, tc in enumerate(test_cases):
                assert "description" in tc and isinstance(tc["description"], str) and tc["description"].strip(), (
                    f"Test case #{idx} in {task_id} missing description"
                )
                assert "test_code" in tc and isinstance(tc["test_code"], str) and tc["test_code"].strip(), (
                    f"Test case #{idx} in {task_id} missing test_code"
                )

    def test_unique_task_ids(self):
        """Verify that every task ID across all files is globally unique."""
        tasks = load_all_tasks()
        seen_ids = set()
        duplicates = []
        for task in tasks:
            tid = task["id"]
            if tid in seen_ids:
                duplicates.append(tid)
            seen_ids.add(tid)
        assert not duplicates, f"Found duplicate task IDs: {duplicates}"

    def test_starter_code_compiles(self):
        """Verify that starter code templates are valid Python syntax."""
        tasks = load_all_tasks()
        for task in tasks:
            tid = task["id"]
            try:
                compile(task["starter_code"], f"<{tid}_starter>", "exec")
            except SyntaxError as e:
                pytest.fail(f"Syntax error in starter_code for task '{tid}': {e}")


class TestReferenceSolutionsAndTestCases:
    """Test suite executing task test suites against reference solutions and validating tests."""

    @pytest.fixture(scope="class")
    def reference_solutions(self):
        from backend.tests.reference_solutions import REFERENCE_SOLUTIONS
        return REFERENCE_SOLUTIONS

    def test_all_tasks_have_reference_solution(self, reference_solutions):
        """Ensure every task in content/tasks has a corresponding reference solution."""
        tasks = load_all_tasks()
        missing = [t["id"] for t in tasks if t["id"] not in reference_solutions]
        assert not missing, f"Missing reference solutions for tasks: {missing}"

    @pytest.mark.parametrize("task", load_all_tasks(), ids=lambda t: t["id"])
    def test_task_reference_solution_passes_all_tests(self, task, reference_solutions):
        """Verify that running reference solution passes 100% of its test cases."""
        tid = task["id"]
        assert tid in reference_solutions, f"No reference solution for task {tid}"
        code = reference_solutions[tid]

        # Execute reference solution in clean global scope
        test_globals = {}
        try:
            exec(code, test_globals)
        except Exception as e:
            pytest.fail(f"Failed to execute reference solution for '{tid}': {e}")

        # Execute each test case
        for idx, tc in enumerate(task["test_cases"]):
            test_code = tc["test_code"]
            desc = tc["description"]
            try:
                exec(test_code, test_globals)
            except AssertionError as e:
                pytest.fail(f"Reference solution for '{tid}' failed test #{idx} ('{desc}'): {e}")
            except Exception as e:
                pytest.fail(f"Unexpected exception during test #{idx} ('{desc}') for '{tid}': {e}")

    @pytest.mark.parametrize("task", load_all_tasks(), ids=lambda t: t["id"])
    def test_starter_code_fails_tests(self, task):
        """Verify that uncompleted starter code fails at least one test case or raises an error."""
        starter = task["starter_code"]
        test_globals = {}
        try:
            exec(starter, test_globals)
        except Exception:
            # If executing starter code itself raises (unlikely with 'pass', but acceptable), test passes
            return

        failed = False
        for tc in task["test_cases"]:
            try:
                exec(tc["test_code"], test_globals)
            except (AssertionError, TypeError, AttributeError, NameError, NotImplementedError):
                failed = True
                break
            except Exception:
                failed = True
                break

        assert failed, f"Task '{task['id']}': starter_code surprisingly passed all test cases! Tests might be too trivial."
