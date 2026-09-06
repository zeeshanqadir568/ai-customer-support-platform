"""FastAPI application entrypoint.

Run: uvicorn api.main:app --reload   (after `pip install -e .`)
Docs: http://127.0.0.1:8000/docs
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.routes import chat, health, tickets
from core import db
from core.config import get_settings
from data.seed import seed


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
