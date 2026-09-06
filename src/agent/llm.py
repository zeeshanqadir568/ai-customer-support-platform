"""LLM client seam.

The orchestrator depends on the small ``LLMClient`` protocol below, not on the
Anthropic SDK directly. That keeps the agent loop unit-testable with a scripted
client and no network access.

Both the real and scripted clients return objects that quack like an Anthropic
``Message``: a ``.stop_reason`` string and a ``.content`` list whose blocks have
a ``.type`` of ``"text"`` (with ``.text``) or ``"tool_use"`` (with ``.id``,
``.name``, ``.input``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


class LLMClient(Protocol):
    def create(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        max_tokens: int,
    ) -> Any: ...


class AnthropicLLM:
    """Thin wrapper over the Anthropic SDK."""

    def __init__(self, api_key: str, model: str) -> None:
        import anthropic

        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def create(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        max_tokens: int,
    ) -> Any:
        return self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            tools=tools,
            thinking={"type": "adaptive"},
            messages=messages,
        )


# --- scripted client + block shims (used by tests and the no-key fallback) ---


@dataclass
class TextBlock:
    text: str
    type: str = "text"


@dataclass
class ToolUseBlock:
    name: str
    input: dict[str, Any]
    id: str = "toolu_test"
    type: str = "tool_use"


@dataclass
class FakeMessage:
    content: list[Any]
    stop_reason: str


@dataclass
class ScriptedLLM:
    """Returns pre-canned responses in order, one per ``create`` call.

    Each turn is a list of blocks. ``stop_reason`` is derived: ``tool_use`` if any
    block is a tool call, otherwise ``end_turn``.
    """

    turns: list[list[Any]]
    calls: list[dict[str, Any]] = field(default_factory=list)

    def create(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        max_tokens: int,
    ) -> FakeMessage:
        self.calls.append({"messages": list(messages), "tools": tools})
        if not self.turns:
            raise AssertionError("ScriptedLLM ran out of scripted turns")
        blocks = self.turns.pop(0)
        stop = (
            "tool_use"
            if any(getattr(b, "type", None) == "tool_use" for b in blocks)
            else "end_turn"
        )
        return FakeMessage(content=blocks, stop_reason=stop)
