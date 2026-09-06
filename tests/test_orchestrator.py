"""Tests for the agent loop and its escalation backstops, using a scripted LLM."""

from agent.llm import ScriptedLLM, TextBlock, ToolUseBlock
from agent.orchestrator import SupportAgent
from services import tickets as ticket_service


def _agent(turns, conn, settings):
    return SupportAgent(llm=ScriptedLLM(turns=turns), conn=conn, settings=settings)


def test_resolves_after_tool_lookup(conn, settings):
    agent = _agent(
        [
            [ToolUseBlock(name="lookup_order", input={"order_id": "ORD-1002"})],
            [TextBlock(text="Your USB-C hub shipped 3 days ago and is on its way.")],
        ],
        conn,
        settings,
    )
    result = agent.run("Where is my order ORD-1002?")

    assert result.resolved is True
    assert result.escalated is False
    assert result.ticket_id is None
    assert result.steps == 2
    assert [c.name for c in result.tool_calls] == ["lookup_order"]
    assert "shipped" in result.reply


def test_model_can_escalate_itself(conn, settings):
    agent = _agent(
        [
            [
                ToolUseBlock(
                    name="escalate_to_human",
                    input={"summary": "Customer threatens legal action over delay.",
                           "reason": "complaint"},
                )
            ]
        ],
        conn,
        settings,
    )
    result = agent.run("This is unacceptable, I want to speak to your legal team.")

    assert result.escalated is True
    assert result.resolved is False
    assert result.ticket_id is not None
    assert f"#{result.ticket_id}" in result.reply

    ticket = ticket_service.get_ticket(conn, result.ticket_id)
    assert ticket["reason"] == "complaint"
    assert ticket["status"] == "open"


def test_sensitive_tool_is_blocked_and_escalated(conn, settings):
    agent = _agent(
        [
            [
                ToolUseBlock(
                    name="issue_refund",
                    input={"order_id": "ORD-1001", "reason": "changed my mind"},
                )
            ]
        ],
        conn,
        settings,
    )
    result = agent.run("Just refund ORD-1001 now.")

    assert result.escalated is True
    assert result.ticket_id is not None
    blocked = [c for c in result.tool_calls if c.name == "issue_refund"][0]
    assert "blocked" in blocked.outcome

    ticket = ticket_service.get_ticket(conn, result.ticket_id)
    assert ticket["reason"] == "sensitive_action"


def test_runaway_loop_hits_max_steps(conn, settings):
    turns = [
        [ToolUseBlock(name="lookup_customer", input={"email": "ada@example.com"})]
        for _ in range(settings.max_agent_steps)
    ]
    agent = _agent(turns, conn, settings)
    result = agent.run("hello?")

    assert result.escalated is True
    assert result.steps == settings.max_agent_steps
    ticket = ticket_service.get_ticket(conn, result.ticket_id)
    assert ticket["reason"] == "max_steps"


def test_history_is_passed_back_to_the_model(conn, settings):
    llm = ScriptedLLM(turns=[[TextBlock(text="Hi Ada, how can I help?")]])
    agent = SupportAgent(llm=llm, conn=conn, settings=settings)
    history = [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": [{"type": "text", "text": "Hello!"}]},
    ]
    agent.run("Are you still there?", history=history)

    sent = llm.calls[0]["messages"]
    assert sent[0]["content"] == "Hi"
    assert sent[-1]["content"] == "Are you still there?"
