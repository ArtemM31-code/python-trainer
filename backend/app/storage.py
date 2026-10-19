"""Storage manager for loading tasks and tracking user progress."""

import datetime
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from backend.app.config import PROGRESS_FILE, TASKS_DIR

logger = logging.getLogger(__name__)


class TopicMeta(BaseModel):
    id: str
    title: str
    description: str
    order: int = 100


class TopicSummary(BaseModel):
    id: str
    title: str
    description: str
    tasks_count: int = 0
    completed_count: int = 0


class TaskSummary(BaseModel):
    id: str
    topic_id: str
    title: str
    difficulty: str = "easy"
    completed: bool = False


class TaskDetail(BaseModel):
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
    test_cases: List[Dict[str, Any]] = Field(default_factory=list)


class UserProgressData(BaseModel):
    completed_tasks: List[str] = Field(default_factory=list)
    user_solutions: Dict[str, str] = Field(default_factory=dict)
    last_active_task: Optional[str] = None
    updated_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())


class ProgressReport(BaseModel):
    total_tasks: int
    completed_tasks: int
    percentage: float
    completed_ids: List[str]


class TaskStorage:
    """Manages task catalog and user progress persistence."""

    def __init__(self, tasks_dir: Path = TASKS_DIR, progress_file: Path = PROGRESS_FILE):
        self.tasks_dir = tasks_dir
        self.progress_file = progress_file
        self._topics: Dict[str, TopicMeta] = {}
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._topic_tasks: Dict[str, List[str]] = {}
        self._last_loaded_mtime: float = 0.0

        self.reload_if_needed()

    def _get_directory_mtime(self) -> float:
        """Get latest mtime of tasks directory and files."""
        if not self.tasks_dir.exists():
            return 0.0
        max_mtime = self.tasks_dir.stat().st_mtime
        try:
            for item in self.tasks_dir.glob("*.json"):
                max_mtime = max(max_mtime, item.stat().st_mtime)
        except Exception:
            pass
        return max_mtime

    def reload_if_needed(self, force: bool = False) -> None:
        """Reload tasks from disk if files were modified."""
        current_mtime = self._get_directory_mtime()
        if force or current_mtime > self._last_loaded_mtime or not self._tasks:
            self._load_all_tasks()
            self._last_loaded_mtime = current_mtime

    def _load_all_tasks(self) -> None:
        """Load and parse all task JSON files from content/tasks."""
        self._topics.clear()
        self._tasks.clear()
        self._topic_tasks.clear()

        if not self.tasks_dir.exists():
            return

        json_files = sorted(list(self.tasks_dir.glob("*.json")))
        for file_idx, filepath in enumerate(json_files):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.loads(f.read(), strict=False)

                # Try to extract topic order from file prefix (e.g. '01_basics.json' -> 1)
                default_order = file_idx + 1
                stem = filepath.stem
                if stem[:2].isdigit():
                    try:
                        default_order = int(stem[:2])
                    except ValueError:
                        pass

                # Case 1: Topic container with tasks list
                if isinstance(data, dict) and "tasks" in data:
                    topic_id = data.get("id") or stem
                    topic_title = data.get("title") or topic_id.capitalize()
                    topic_desc = data.get("description") or ""
                    topic_order = data.get("order", default_order)

                    self._topics[topic_id] = TopicMeta(
                        id=topic_id,
                        title=topic_title,
                        description=topic_desc,
                        order=topic_order,
                    )
                    self._topic_tasks.setdefault(topic_id, [])

                    for task_dict in data.get("tasks", []):
                        if not isinstance(task_dict, dict) or "id" not in task_dict:
                            continue
                        tid = task_dict["id"]
                        task_dict["topic_id"] = task_dict.get("topic_id") or topic_id
                        self._tasks[tid] = task_dict
                        if tid not in self._topic_tasks[topic_id]:
                            self._topic_tasks[topic_id].append(tid)

                # Case 2: List of task objects
                elif isinstance(data, list):
                    first_task = data[0] if data and isinstance(data[0], dict) else {}
                    topic_id = first_task.get("topic_id") or stem
                    topic_title = first_task.get("topic_title") or topic_id.replace("_", " ").capitalize()
                    topic_desc = first_task.get("topic_description") or ""

                    if topic_id not in self._topics:
                        self._topics[topic_id] = TopicMeta(
                            id=topic_id,
                            title=topic_title,
                            description=topic_desc,
                            order=default_order,
                        )
                    self._topic_tasks.setdefault(topic_id, [])

                    for task_dict in data:
                        if not isinstance(task_dict, dict) or "id" not in task_dict:
                            continue
                        tid = task_dict["id"]
                        t_topic = task_dict.get("topic_id") or topic_id
                        task_dict["topic_id"] = t_topic
                        self._tasks[tid] = task_dict
                        self._topic_tasks.setdefault(t_topic, [])
                        if tid not in self._topic_tasks[t_topic]:
                            self._topic_tasks[t_topic].append(tid)

                # Case 3: Single task object
                elif isinstance(data, dict) and "id" in data:
                    tid = data["id"]
                    topic_id = data.get("topic_id") or stem
                    data["topic_id"] = topic_id
                    self._topics.setdefault(
                        topic_id,
                        TopicMeta(
                            id=topic_id,
                            title=topic_id.capitalize(),
                            description="",
                            order=default_order,
                        ),
                    )
                    self._tasks[tid] = data
                    self._topic_tasks.setdefault(topic_id, [])
                    if tid not in self._topic_tasks[topic_id]:
                        self._topic_tasks[topic_id].append(tid)

            except Exception as e:
                logger.error(f"Error loading task file {filepath}: {e}")

    def get_user_progress(self) -> UserProgressData:
        """Load user progress from JSON file."""
        if not self.progress_file.exists():
            return UserProgressData()

        try:
            with open(self.progress_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return UserProgressData(**data)
        except Exception as e:
            logger.warning(f"Could not read user progress ({e}), returning default empty progress.")
            return UserProgressData()

    def save_user_progress(self, progress: UserProgressData) -> None:
        """Save user progress to JSON file atomically."""
        progress.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        temp_file = self.progress_file.with_suffix(".tmp")
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(progress.model_dump(), f, ensure_ascii=False, indent=2)
            temp_file.replace(self.progress_file)
        except Exception as e:
            logger.error(f"Failed to save user progress: {e}")
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass

    def get_topics(self) -> List[TopicSummary]:
        """Get summary of all topics with task completion counts."""
        self.reload_if_needed()
        progress = self.get_user_progress()
        completed_set = set(progress.completed_tasks)

        sorted_topics = sorted(self._topics.values(), key=lambda t: (t.order, t.id))
        summaries = []
        for topic in sorted_topics:
            task_ids = self._topic_tasks.get(topic.id, [])
            completed_in_topic = sum(1 for tid in task_ids if tid in completed_set)
            summaries.append(
                TopicSummary(
                    id=topic.id,
                    title=topic.title,
                    description=topic.description,
                    tasks_count=len(task_ids),
                    completed_count=completed_in_topic,
                )
            )
        return summaries

    def get_tasks(self, topic_id: Optional[str] = None) -> List[TaskSummary]:
        """Get list of task summaries, optionally filtered by topic."""
        self.reload_if_needed()
        progress = self.get_user_progress()
        completed_set = set(progress.completed_tasks)

        result: List[TaskSummary] = []
        if topic_id:
            task_ids = self._topic_tasks.get(topic_id, [])
            for tid in task_ids:
                raw = self._tasks.get(tid)
                if raw:
                    result.append(
                        TaskSummary(
                            id=tid,
                            topic_id=topic_id,
                            title=raw.get("title", tid),
                            difficulty=raw.get("difficulty", "easy"),
                            completed=(tid in completed_set),
                        )
                    )
        else:
            # All tasks ordered by topic order
            sorted_topics = sorted(self._topics.values(), key=lambda t: (t.order, t.id))
            seen = set()
            for topic in sorted_topics:
                for tid in self._topic_tasks.get(topic.id, []):
                    if tid in seen:
                        continue
                    seen.add(tid)
                    raw = self._tasks.get(tid)
                    if raw:
                        result.append(
                            TaskSummary(
                                id=tid,
                                topic_id=topic.id,
                                title=raw.get("title", tid),
                                difficulty=raw.get("difficulty", "easy"),
                                completed=(tid in completed_set),
                            )
                        )
            # Add any tasks not attached to defined topics
            for tid, raw in self._tasks.items():
                if tid not in seen:
                    result.append(
                        TaskSummary(
                            id=tid,
                            topic_id=raw.get("topic_id", "general"),
                            title=raw.get("title", tid),
                            difficulty=raw.get("difficulty", "easy"),
                            completed=(tid in completed_set),
                        )
                    )
        return result

    def get_task(self, task_id: str) -> Optional[TaskDetail]:
        """Get detailed task information by task_id."""
        self.reload_if_needed()
        raw = self._tasks.get(task_id)
        if not raw:
            return None

        progress = self.get_user_progress()
        completed = task_id in set(progress.completed_tasks)
        user_sol = progress.user_solutions.get(task_id)
        test_cases = raw.get("test_cases", [])

        return TaskDetail(
            id=raw.get("id", task_id),
            topic_id=raw.get("topic_id", ""),
            title=raw.get("title", task_id),
            difficulty=raw.get("difficulty", "easy"),
            theory=raw.get("theory", ""),
            instructions=raw.get("instructions", ""),
            starter_code=raw.get("starter_code", ""),
            hint=raw.get("hint", ""),
            tests_count=len(test_cases),
            completed=completed,
            user_solution=user_sol if user_sol is not None else raw.get("starter_code", ""),
            test_cases=test_cases,
        )

    def record_submission(self, task_id: str, code: str, passed: bool) -> bool:
        """
        Record user submission code and completion status.
        Returns True if all tasks in the platform are completed.
        """
        self.reload_if_needed()
        progress = self.get_user_progress()
        progress.user_solutions[task_id] = code
        progress.last_active_task = task_id

        if passed and task_id not in progress.completed_tasks:
            progress.completed_tasks.append(task_id)

        self.save_user_progress(progress)

        total_tasks = len(self._tasks)
        completed_count = len(progress.completed_tasks)
        all_completed = (total_tasks > 0) and (completed_count >= total_tasks)
        return all_completed

    def reset_progress(self) -> None:
        """Reset all user progress."""
        progress = UserProgressData(
            completed_tasks=[],
            user_solutions={},
            last_active_task=None,
        )
        self.save_user_progress(progress)

    def get_progress_report(self) -> ProgressReport:
        """Get aggregated overall progress statistics."""
        self.reload_if_needed()
        progress = self.get_user_progress()
        total_tasks = len(self._tasks)
        completed_ids = [tid for tid in progress.completed_tasks if tid in self._tasks]
        completed_count = len(completed_ids)
        percentage = round((completed_count / total_tasks * 100), 1) if total_tasks > 0 else 0.0

        return ProgressReport(
            total_tasks=total_tasks,
            completed_tasks=completed_count,
            percentage=percentage,
            completed_ids=completed_ids,
        )


# Global singleton instance for application use
storage = TaskStorage()
