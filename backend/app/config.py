"""Application configuration and filesystem paths."""

import os
from pathlib import Path

# Base project directory (python-trainer/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Core subdirectories
BACKEND_DIR = BASE_DIR / "backend"
APP_DIR = BACKEND_DIR / "app"
CONTENT_DIR = BASE_DIR / "content"
TASKS_DIR = CONTENT_DIR / "tasks"
FRONTEND_DIR = BASE_DIR / "frontend"
DATA_DIR = BASE_DIR / "data"

# Progress persistence file
PROGRESS_FILE = BASE_DIR / "user_progress.json"

# Execution sandbox limits
DEFAULT_TIMEOUT_SECONDS = 4.0
MAX_OUTPUT_LENGTH = 100_000

# Server settings
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000

# Ensure essential directories exist
TASKS_DIR.mkdir(parents=True, exist_ok=True)
FRONTEND_DIR.mkdir(parents=True, exist_ok=True)
