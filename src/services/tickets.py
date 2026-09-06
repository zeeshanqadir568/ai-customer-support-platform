"""Ticket persistence. A ticket is what the platform produces whenever the AI
hands a case to a human."""

from __future__ import annotations

import json
import sqlite3
from typing import Any


def create_ticket(
    conn: sqlite3.Connection,
    *,
    subject: str,
    body: str,
    reason: str,
    customer_email: str | None = None,
    transcript: list[dict[str, Any]] | None = None,
) -> dict:
    cur = conn.execute(
        """
        INSERT INTO tickets (customer_email, subject, body, reason, transcript)
        VALUES (?, ?, ?, ?, ?)
        """,
        (customer_email, subject, body, reason, json.dumps(transcript or [])),
    )
    conn.commit()
    return get_ticket(conn, cur.lastrowid)  # type: ignore[arg-type]


def get_ticket(conn: sqlite3.Connection, ticket_id: int) -> dict | None:
    row = conn.execute(
        "SELECT * FROM tickets WHERE id = ?", (ticket_id,)
    ).fetchone()
    return dict(row) if row is not None else None


def list_tickets(
    conn: sqlite3.Connection, status: str | None = None
) -> list[dict]:
    if status:
        rows = conn.execute(
            "SELECT * FROM tickets WHERE status = ? ORDER BY created_at DESC",
            (status,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM tickets ORDER BY created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def update_status(
    conn: sqlite3.Connection, ticket_id: int, status: str
) -> dict | None:
    conn.execute(
        "UPDATE tickets SET status = ?, updated_at = datetime('now') WHERE id = ?",
        (status, ticket_id),
    )
    conn.commit()
    return get_ticket(conn, ticket_id)
