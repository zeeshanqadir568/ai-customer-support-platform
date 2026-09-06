"""FastAPI dependencies: settings, per-request DB connection, LLM client, and a
tiny in-memory conversation store.

The LLM and store providers are overridden in tests via
``app.dependency_overrides``.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from fastapi import Depends, HTTPException

from agent.llm import AnthropicLLM, LLMClient
from core import db
from core.config import Settings, get_settings


def settings_dep() -> Settings:
    return get_settings()


def get_db(settings: Settings = Depends(settings_dep)) -> Iterator[Any]:
    conn = db.connect(settings.database_path)
    try:
        yield conn
    finally:
        conn.close()


def get_llm(settings: Settings = Depends(settings_dep)) -> LLMClient:
    if not settings.llm_configured:
        raise HTTPException(
            status_code=503,
            detail="LLM is not configured. Set ANTHROPIC_API_KEY to enable /chat.",
        )
    return AnthropicLLM(api_key=settings.anthropic_api_key, model=settings.model)


class ConversationStore:
    """Keeps resolved-conversation transcripts in process memory, keyed by id."""

    def __init__(self) -> None:
        self._data: dict[str, list[dict[str, Any]]] = {}

    def get(self, conversation_id: str) -> list[dict[str, Any]] | None:
        return self._data.get(conversation_id)

    def put(self, conversation_id: str, transcript: list[dict[str, Any]]) -> None:
        self._data[conversation_id] = transcript

    def drop(self, conversation_id: str) -> None:
        self._data.pop(conversation_id, None)


_store = ConversationStore()


def get_store() -> ConversationStore:
    return _store
