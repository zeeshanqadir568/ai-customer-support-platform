"""The support agent: a reason -> act loop over the Anthropic Messages API with
deterministic backstops for escalation.

The model drives resolution by calling tools. Three things force a human handoff
regardless of what the model wants:

1. It calls ``escalate_to_human`` itself (low confidence, complaints, security...).
2. It calls a sensitive tool (``issue_refund``) - intercepted, never executed,
   turned into a ticket.
3. It runs past ``max_agent_steps`` without finishing - safety valve.

Every handoff opens a ticket with a transcript snapshot.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from pydantic import BaseModel

from agent.llm import LLMClient
from agent.prompts import SUPPORT_SYSTEM
from agent.tools import ESCALATION_TOOL, SENSITIVE_TOOLS, TOOL_SPECS, dispatch
from core.config import Settings
from services import tickets


class ToolCall(BaseModel):
    step: int
    name: str
    input: dict[str, Any]
    outcome: str


class AgentResult(BaseModel):
    reply: str
    resolved: bool
    escalated: bool
    ticket_id: int | None = None
    steps: int
    tool_calls: list[ToolCall] = []


def _assistant_param(blocks: list[Any]) -> list[dict[str, Any]]:
    """Normalise response content blocks into message params to replay."""
    out: list[dict[str, Any]] = []
    for b in blocks:
        if hasattr(b, "model_dump"):  # real Anthropic SDK block
            out.append(b.model_dump(exclude_none=True))
            continue
        if b.type == "text":
            out.append({"type": "text", "text": b.text})
        elif b.type == "tool_use":
            out.append(
                {"type": "tool_use", "id": b.id, "name": b.name, "input": b.input}
            )
    return out


def _text_of(blocks: list[Any]) -> str:
    parts = [b.text for b in blocks if getattr(b, "type", None) == "text"]
    return "\n".join(p for p in parts if p).strip()


def _short(payload: str, limit: int = 160) -> str:
    return payload if len(payload) <= limit else payload[: limit - 3] + "..."


def _snapshot(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """A JSON-safe copy of the transcript to store on the ticket."""
    return [{"role": m["role"], "content": m["content"]} for m in messages]


class SupportAgent:
    def __init__(
        self, llm: LLMClient, conn: sqlite3.Connection, settings: Settings
    ) -> None:
        self._llm = llm
        self._conn = conn
        self._settings = settings
        # Full message list after the most recent run(). Callers that want to
        # continue a conversation persist this and pass it back as `history`.
        self.transcript: list[dict[str, Any]] = []

    # -- public ---------------------------------------------------------

    def run(
        self,
        message: str,
        *,
        history: list[dict[str, Any]] | None = None,
        customer_email: str | None = None,
    ) -> AgentResult:
        messages: list[dict[str, Any]] = list(history or [])
        messages.append({"role": "user", "content": message})
        calls: list[ToolCall] = []
        max_steps = self._settings.max_agent_steps

        for step in range(1, max_steps + 1):
            resp = self._llm.create(
                system=SUPPORT_SYSTEM,
                messages=messages,
                tools=TOOL_SPECS,
                max_tokens=self._settings.agent_max_tokens,
            )
            messages.append(
                {"role": "assistant", "content": _assistant_param(resp.content)}
            )

            if resp.stop_reason != "tool_use":
                self.transcript = messages
                return AgentResult(
                    reply=_text_of(resp.content)
                    or "I'm sorry, I don't have an answer for that.",
                    resolved=True,
                    escalated=False,
                    steps=step,
                    tool_calls=calls,
                )

            tool_uses = [
                b for b in resp.content if getattr(b, "type", None) == "tool_use"
            ]
            results: list[dict[str, Any]] = []
            forced: tuple[str, str] | None = None

            for tu in tool_uses:
                tu_input = tu.input if isinstance(tu.input, dict) else {}

                if tu.name == ESCALATION_TOOL:
                    summary = tu_input.get("summary", "(no summary provided)")
                    reason = tu_input.get("reason", "low_confidence")
                    calls.append(
                        ToolCall(
                            step=step, name=tu.name, input=tu_input, outcome="escalated"
                        )
                    )
                    return self._handoff(
                        customer_email, summary, reason, messages, step, calls
                    )

                if tu.name in SENSITIVE_TOOLS:
                    results.append(
                        _tool_result(
                            tu.id,
                            "This action requires human approval. The case has "
                            "been routed to a support specialist.",
                        )
                    )
                    calls.append(
                        ToolCall(
                            step=step,
                            name=tu.name,
                            input=tu_input,
                            outcome="blocked: needs human approval",
                        )
                    )
                    forced = (
                        f"Customer wants {tu.name} for order "
                        f"{tu_input.get('order_id', '?')}: "
                        f"{tu_input.get('reason', '(no reason given)')}",
                        "sensitive_action",
                    )
                    continue

                payload = dispatch(self._conn, tu.name, tu_input)
                results.append(_tool_result(tu.id, payload))
                calls.append(
                    ToolCall(
                        step=step,
                        name=tu.name,
                        input=tu_input,
                        outcome=_short(payload),
                    )
                )

            messages.append({"role": "user", "content": results})

            if forced is not None:
                return self._handoff(
                    customer_email, forced[0], forced[1], messages, step, calls
                )

        # ran out of steps
        return self._handoff(
            customer_email,
            f"Agent could not resolve after {max_steps} steps. "
            f"Original message: {message}",
            "max_steps",
            messages,
            max_steps,
            calls,
        )

    # -- internals ----------------------------------------------------

    def _handoff(
        self,
        customer_email: str | None,
        summary: str,
        reason: str,
        messages: list[dict[str, Any]],
        step: int,
        calls: list[ToolCall],
    ) -> AgentResult:
        self.transcript = messages
        ticket = tickets.create_ticket(
            self._conn,
            customer_email=customer_email,
            subject=summary[:120],
            body=summary,
            reason=reason,
            transcript=_snapshot(messages),
        )
        return AgentResult(
            reply=(
                f"I've opened ticket #{ticket['id']} and a support specialist "
                f"will follow up with you shortly."
            ),
            resolved=False,
            escalated=True,
            ticket_id=ticket["id"],
            steps=step,
            tool_calls=calls,
        )


def _tool_result(tool_use_id: str, content: str) -> dict[str, Any]:
    return {
        "type": "tool_result",
        "tool_use_id": tool_use_id,
        "content": content,
    }


def dumps(result: AgentResult) -> str:
    return json.dumps(result.model_dump())
