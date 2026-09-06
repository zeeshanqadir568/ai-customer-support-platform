"""Shared fixtures. Every test gets an isolated seeded SQLite database and never
touches the network."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator

import pytest

from core import db
from core.config import Settings
from data.seed import seed


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(
        anthropic_api_key="test-key",
        model="claude-opus-5",
        max_agent_steps=6,
        agent_max_tokens=1024,
        database_path=str(tmp_path / "test.db"),
        seed_on_startup=False,
    )


@pytest.fixture
def conn(settings: Settings) -> Iterator[sqlite3.Connection]:
    connection = db.connect(settings.database_path)
    db.init_db(connection)
    seed(connection)
    try:
        yield connection
    finally:
        connection.close()


@pytest.fixture
def client(settings: Settings, conn: sqlite3.Connection):
    """TestClient with DB + settings wired to the fixtures. Individual tests
    override ``get_llm`` with a ScriptedLLM."""
    from fastapi.testclient import TestClient

    from api import deps
    from api.deps import get_db, get_store, settings_dep
    from api.main import app

    store = deps.ConversationStore()
    app.dependency_overrides[settings_dep] = lambda: settings
    app.dependency_overrides[get_db] = lambda: conn
    app.dependency_overrides[get_store] = lambda: store

    # No context manager: skip lifespan so the app never opens the real
    # support.db. Routes use the overridden get_db above.
    yield TestClient(app)

    app.dependency_overrides.clear()
