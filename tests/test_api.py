"""End-to-end HTTP tests. The LLM is a ScriptedLLM injected via dependency
override; nothing hits the network."""

from agent.llm import ScriptedLLM, TextBlock, ToolUseBlock
from api.deps import get_llm
from api.main import app


def _use_llm(*turns):
    app.dependency_overrides[get_llm] = lambda: ScriptedLLM(turns=list(turns))


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_index_serves_html(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "AI Customer Support Platform" in resp.text


def test_config_reports_llm_state(client, settings):
    settings.anthropic_api_key = "test-key"
    resp = client.get("/config")
    assert resp.status_code == 200
    body = resp.json()
    assert body["llm_configured"] is True
    assert body["model"] == settings.model


def test_chat_resolved_flow(client):
    _use_llm(
        [ToolUseBlock(name="lookup_order", input={"order_id": "ORD-1002"})],
        [TextBlock(text="Your USB-C hub shipped 3 days ago.")],
    )
    resp = client.post("/chat", json={"message": "Where's ORD-1002?"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["resolved"] is True
    assert body["escalated"] is False
    assert body["conversation_id"]
    assert body["tool_calls"][0]["name"] == "lookup_order"


def test_chat_escalation_creates_visible_ticket(client):
    _use_llm(
        [
            ToolUseBlock(
                name="escalate_to_human",
                input={"summary": "Suspected account takeover.",
                       "reason": "account_security"},
            )
        ]
    )
    resp = client.post(
        "/chat",
        json={"message": "Someone changed my password!", "customer_email": "ada@example.com"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["escalated"] is True
    ticket_id = body["ticket_id"]
    assert ticket_id is not None

    tickets = client.get("/tickets").json()
    assert any(t["id"] == ticket_id and t["reason"] == "account_security" for t in tickets)


def test_chat_requires_llm_configuration(client, settings):
    # Point settings at an unconfigured LLM and remove the override so the real
    # get_llm dependency runs its guard.
    settings.anthropic_api_key = ""
    app.dependency_overrides.pop(get_llm, None)

    resp = client.post("/chat", json={"message": "hi"})
    assert resp.status_code == 503


def test_chat_rejects_empty_message(client):
    _use_llm([TextBlock(text="unused")])
    resp = client.post("/chat", json={"message": "   "})
    assert resp.status_code == 422


def test_chat_turns_agent_failure_into_clean_error(client):
    class BoomLLM:
        def create(self, **kwargs):
            raise RuntimeError("model connection dropped")

    app.dependency_overrides[get_llm] = lambda: BoomLLM()
    try:
        resp = client.post("/chat", json={"message": "Where is ORD-1002?"})
    finally:
        app.dependency_overrides.pop(get_llm, None)

    assert resp.status_code == 502
    detail = resp.json()["detail"]
    assert "try again" in detail.lower()
    assert "traceback" not in detail.lower()


def test_ticket_update_status(client):
    created = client.post(
        "/tickets", json={"subject": "S", "body": "B", "reason": "manual"}
    ).json()
    resp = client.patch(f"/tickets/{created['id']}", json={"status": "resolved"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "resolved"


def test_ticket_not_found(client):
    assert client.get("/tickets/999999").status_code == 404
