"""Tool schemas exposed to the model, plus a dispatcher for the read-only ones.

Two tools are *not* dispatched here because the orchestrator intercepts them:
- ``issue_refund``    -> sensitive; never executed by the AI, forces escalation.
- ``escalate_to_human`` -> ends the loop and opens a ticket.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from services import business

# Tools whose call the orchestrator handles itself.
SENSITIVE_TOOLS = {"issue_refund"}
ESCALATION_TOOL = "escalate_to_human"

TOOL_SPECS: list[dict[str, Any]] = [
    {
        "name": "lookup_customer",
        "description": "Look up a customer by email address. Returns their name "
        "and plan, or null if there is no such customer.",
        "input_schema": {
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "Customer email address."}
            },
            "required": ["email"],
        },
    },
    {
        "name": "lookup_order",
        "description": "Get one order by its id (e.g. 'ORD-1001'), or list every "
        "order for a customer by email. Provide exactly one of the two.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "email": {"type": "string"},
            },
        },
    },
    {
        "name": "check_refund_eligibility",
        "description": "Check whether an order qualifies for an automatic refund "
        "under policy (delivered, within the return window, under the amount "
        "limit, not already refunded).",
        "input_schema": {
            "type": "object",
            "properties": {"order_id": {"type": "string"}},
            "required": ["order_id"],
        },
    },
    {
        "name": "issue_refund",
        "description": "Request that a refund be paid out for an order. This "
        "requires human approval and will route the case to a specialist; it "
        "does not move any money by itself.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "reason": {"type": "string"},
            },
            "required": ["order_id", "reason"],
        },
    },
    {
        "name": ESCALATION_TOOL,
        "description": "Hand this conversation to a human support specialist and "
        "stop. Use for anything you cannot resolve confidently or should not "
        "resolve alone.",
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "One or two sentences a human can act on.",
                },
                "reason": {
                    "type": "string",
                    "description": "Short category, e.g. 'refund_review', "
                    "'account_security', 'complaint', 'low_confidence'.",
                },
            },
            "required": ["summary", "reason"],
        },
    },
]


def dispatch(conn: sqlite3.Connection, name: str, tool_input: dict[str, Any]) -> str:
    """Run a read-only tool and return a JSON string for the tool_result block."""
    if name == "lookup_customer":
        result: Any = business.lookup_customer(conn, tool_input["email"])
    elif name == "lookup_order":
        result = business.lookup_order(
            conn,
            order_id=tool_input.get("order_id"),
            email=tool_input.get("email"),
        )
    elif name == "check_refund_eligibility":
        result = business.check_refund_eligibility(conn, tool_input["order_id"])
    else:
        result = {"error": f"Unknown tool {name!r}."}
    return json.dumps(result, default=str)
