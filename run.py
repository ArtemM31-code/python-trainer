#!/usr/bin/env python3
"""Main launch script for Python Interactive Trainer.

Starts the FastAPI server with uvicorn and automatically opens the application in the browser.
"""

import argparse
import sys
import threading
import time
import webbrowser
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import uvicorn
from backend.app.config import DEFAULT_HOST, DEFAULT_PORT


def open_browser(url: str, delay: float = 1.2):
    """Wait for server to bind then open browser."""
    time.sleep(delay)
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"Could not automatically open browser: {e}")


def main():
    parser = argparse.ArgumentParser(description="Python Interactive Trainer Server")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"Host to bind (default: {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Port to bind (default: {DEFAULT_PORT})")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically open browser")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload")
    args = parser.parse_args()

    url = f"http://{args.host}:{args.port}"
    print(f"\n=======================================================")
    print(f"  Python Interactive Trainer starting at {url}")
    print(f"  Interactive API Docs: {url}/docs")
    print(f"=======================================================\n")

    if not args.no_browser:
        browser_thread = threading.Thread(target=open_browser, args=(url,), daemon=True)
        browser_thread.start()

    reload_mode = not args.no_reload
    uvicorn.run(
        "backend.app.main:app",
        host=args.host,
        port=args.port,
        reload=reload_mode,
        reload_dirs=[str(PROJECT_ROOT / "backend"), str(PROJECT_ROOT / "frontend")] if reload_mode else None,
    )


if __name__ == "__main__":
    main()
