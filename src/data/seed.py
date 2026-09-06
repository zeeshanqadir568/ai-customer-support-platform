"""Seed demo customers and orders so the agent has something to look up.

Idempotent: safe to call on every startup. Dates are computed relative to
"now" so refund-window rules stay meaningful over time.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone


def _iso(days_ago: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


CUSTOMERS = [
    ("ada@example.com", "Ada Lovelace", "pro"),
    ("grace@example.com", "Grace Hopper", "free"),
    ("alan@example.com", "Alan Turing", "enterprise"),
]

# (id, customer_email, item, amount, status, ordered_days_ago, delivered_days_ago, refunded)
ORDERS = [
    ("ORD-1001", "ada@example.com", "Wireless keyboard", 79.00, "delivered", 12, 8, 0),
    ("ORD-1002", "ada@example.com", "USB-C hub", 45.50, "shipped", 3, None, 0),
    ("ORD-1003", "grace@example.com", "Laptop stand", 34.99, "delivered", 90, 84, 0),
    ("ORD-1004", "grace@example.com", "Mechanical mouse", 59.00, "delivered", 5, 2, 1),
    ("ORD-1005", "alan@example.com", "4K monitor", 420.00, "processing", 1, None, 0),
]


def seed(conn: sqlite3.Connection) -> None:
    for email, name, plan in CUSTOMERS:
        conn.execute(
            "INSERT OR IGNORE INTO customers (email, name, plan) VALUES (?, ?, ?)",
            (email, name, plan),
        )

    for oid, email, item, amount, status, ordered, delivered, refunded in ORDERS:
        conn.execute(
            """
            INSERT OR IGNORE INTO orders
                (id, customer_email, item, amount, status, ordered_at, delivered_at, refunded)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                oid,
                email,
                item,
                amount,
                status,
                _iso(ordered),
                _iso(delivered) if delivered is not None else None,
                refunded,
            ),
        )
    conn.commit()
