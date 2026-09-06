"""FastAPI application entrypoint.

Run:    python -m app         (from the repo root, after `pip install -e .`)
   or:  uvicorn api.main:app --reload
Web UI: http://localhost:8000/
Docs:   http://localhost:8000/docs
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse

from api.routes import chat, health, tickets
from core import db
from core.config import get_settings
from data.seed import seed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WEB_DIR = Path(__file__).parent / "web"


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    conn = db.connect(settings.database_path)
    try:
        db.init_db(conn)
        if settings.seed_on_startup:
            seed(conn)
    finally:
        conn.close()
    if not settings.llm_configured:
        logger.warning(
            "ANTHROPIC_API_KEY is not set - POST /chat will return 503. "
            "The web UI, support queue, and ticket APIs still work."
        )
    yield


app = FastAPI(
    title="AI Customer Support Platform",
    description=(
        "Agentic AI customer support: the agent reasons, calls business tools, "
        "and escalates to a human ticket when it should not act alone."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(tickets.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Last-resort backstop: never leak a stack trace to the browser."""
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "detail": (
                "Something went wrong handling this request "
                f"({type(exc).__name__}). Check the server logs for details."
            )
        },
    )


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    """Serve the single-page demo UI."""
    return FileResponse(WEB_DIR / "index.html")
