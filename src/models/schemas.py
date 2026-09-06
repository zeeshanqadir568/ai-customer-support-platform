"""Pydantic request/response models for the HTTP API."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

TicketStatus = Literal["open", "in_progress", "resolved"]


# --- chat ------------------------------------------------------------------


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="The customer's message.")
    customer_email: str | None = Field(
        None, description="Known customer identity, if the channel provides one."
    )
    conversation_id: str | None = Field(
        None, description="Pass the id returned by a previous turn to continue it."
    )

    @field_validator("message")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("message must not be empty or whitespace only")
        return stripped


class ToolCallView(BaseModel):
    step: int
    name: str
    input: dict[str, Any]
    outcome: str


class ChatResponse(BaseModel):
    conversation_id: str
    reply: str
    resolved: bool
    escalated: bool
    ticket_id: int | None = None
    steps: int
    tool_calls: list[ToolCallView] = []


# --- tickets -------------------------------------------------------------


class TicketCreate(BaseModel):
    customer_email: str | None = None
    subject: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)
    reason: str = "manual"


class TicketUpdate(BaseModel):
    status: TicketStatus


class Ticket(BaseModel):
    id: int
    customer_email: str | None
    subject: str
    body: str
    reason: str
    status: TicketStatus
    created_at: str
    updated_at: str
