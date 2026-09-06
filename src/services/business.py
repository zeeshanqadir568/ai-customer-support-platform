"""Read-only business lookups the support agent is allowed to call.

These are deliberately plain functions over the SQLite connection so they are
trivial to unit-test and to swap for a real CRM / order service later.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

# A refund can be auto-approved only inside this window and below this amount.
REFUND_WINDOW_DAYS = 30
REFUND_AUTO_APPROVE_MAX = 200.0


def _row_to_dict(row: sqlite3.Row | None) -> dict | None:
    return dict(row) if row is not None else None


def lookup_customer(conn: sqlite3.Connection, email: str) -> dict | None:
    row = conn.execute(
        "SELECT id, email, name, plan, created_at FROM customers WHERE email = ?",
        (email.strip().lower(),),
    ).fetchone()
    return _row_to_dict(row)


def lookup_order(
    conn: sqlite3.Connection,
    order_id: str | None = None,
    email: str | None = None,
) -> dict:
    """Return a single order by id, or all orders for a customer email."""
    if order_id:
        row = conn.execute(
            "SELECT * FROM orders WHERE id = ?", (order_id.strip().upper(),)
        ).fetchone()
        order = _row_to_dict(row)
        if order is None:
            return {"found": False, "reason": f"No order {order_id!r}."}
        return {"found": True, "order": order}

    if email:
        rows = conn.execute(
            "SELECT * FROM orders WHERE customer_email = ? ORDER BY ordered_at DESC",
            (email.strip().lower(),),
        ).fetchall()
        return {"found": bool(rows), "orders": [dict(r) for r in rows]}

    return {"found": False, "reason": "Provide either order_id or email."}


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def check_refund_eligibility(conn: sqlite3.Connection, order_id: str) -> dict:
    row = conn.execute(
        "SELECT * FROM orders WHERE id = ?", (order_id.strip().upper(),)
    ).fetchone()
    if row is None:
        return {"eligible": False, "reason": f"No order {order_id!r}."}

    order = dict(row)

    if order["refunded"]:
        return {"eligible": False, "reason": "This order was already refunded."}

    if order["status"] != "delivered":
        return {
            "eligible": False,
            "reason": f"Order is {order['status']}, not delivered yet.",
        }

    delivered_at = order.get("delivered_at")
    if not delivered_at:
        return {"eligible": False, "reason": "No delivery date on record."}

    age_days = (datetime.now(timezone.utc) - _parse_iso(delivered_at)).days
    if age_days > REFUND_WINDOW_DAYS:
        return {
            "eligible": False,
            "reason": f"Delivered {age_days} days ago; outside the "
            f"{REFUND_WINDOW_DAYS}-day return window.",
        }

    if order["amount"] > REFUND_AUTO_APPROVE_MAX:
        return {
            "eligible": False,
            "reason": f"Amount {order['amount']} {order['currency']} exceeds the "
            f"auto-approval limit of {REFUND_AUTO_APPROVE_MAX}; needs a specialist.",
            "needs_human": True,
        }

    return {
        "eligible": True,
        "reason": f"Delivered {age_days} days ago, within policy.",
        "amount": order["amount"],
        "currency": order["currency"],
    }
