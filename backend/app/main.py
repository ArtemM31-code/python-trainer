"""Main FastAPI application module."""

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from backend.app.api.routes_execute import router as execute_router
from backend.app.api.routes_progress import router as progress_router
from backend.app.api.routes_tasks import router as tasks_router
from backend.app.config import FRONTEND_DIR

app = FastAPI(
    title="Python Interactive Trainer API",
    description="Interactive Python learning platform with real-time code execution and automated test validation.",
    version="1.0.0",
)

# Enable CORS for local development and browser execution
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(tasks_router)
app.include_router(execute_router)
app.include_router(progress_router)


@app.get("/api/health", tags=["Health"])
def health_check():
    """Health check endpoint to verify backend status."""
    return {"status": "ok", "service": "python-trainer-backend"}


# Mount frontend subdirectories if they exist
css_dir = FRONTEND_DIR / "css"
if css_dir.exists():
    app.mount("/css", StaticFiles(directory=str(css_dir)), name="css")

js_dir = FRONTEND_DIR / "js"
if js_dir.exists():
    app.mount("/js", StaticFiles(directory=str(js_dir)), name="js")


@app.get("/", include_in_schema=False)
def serve_index():
    """Serve main frontend Web IDE single page application."""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))

    return HTMLResponse(
        content="""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <title>Python Interactive Trainer</title>
            <style>
                body {
                    background-color: #0f172a;
                    color: #f8fafc;
                    font-family: system-ui, -apple-system, sans-serif;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    height: 100vh;
                    margin: 0;
                }
                .card {
                    background: #1e293b;
                    padding: 2.5rem;
                    border-radius: 12px;
                    border: 1px solid #334155;
                    max-width: 500px;
                    text-align: center;
                }
                h1 { color: #38bdf8; margin-top: 0; }
                a { color: #38bdf8; text-decoration: none; }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>Python Interactive Trainer</h1>
                <p>Бэкенд успешно запущен и работает!</p>
                <p>API документация: <a href="/docs">/docs</a></p>
                <p>Статус: <code>/api/health</code></p>
            </div>
        </body>
        </html>
        """,
        status_code=200,
    )


# Mount entire frontend static folder if present (fallback for other static assets)
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
