"""SQLite connection helpers and schema management.

The whole app uses one small SQLite file. Every connection sets ``row_factory``
so rows behave like dicts, which keeps the service layer simple.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    email          TEXT NOT NULL UNIQUE,
    name           TEXT NOT NULL,
    plan           TEXT NOT NULL DEFAULT 'free',
    created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS orders (
    id             TEXT PRIMARY KEY,
    customer_email TEXT NOT NULL REFERENCES customers(email),
    item           TEXT NOT NULL,
    amount         REAL NOT NULL,
    currency       TEXT NOT NULL DEFAULT 'USD',
    status         TEXT NOT NULL,          -- processing | shipped | delivered | cancelled
    ordered_at     TEXT NOT NULL,
    delivered_at   TEXT,
    refunded       INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS tickets (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_email TEXT,
    subject        TEXT NOT NULL,
    body           TEXT NOT NULL,
    reason         TEXT NOT NULL,          -- why the AI escalated
    status         TEXT NOT NULL DEFAULT 'open',   -- open | in_progress | resolved
    transcript     TEXT NOT NULL DEFAULT '[]',     -- JSON conversation snapshot
    created_at     TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at     TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def connect(database_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(database_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


@contextmanager
def session(database_path: str) -> Iterator[sqlite3.Connection]:
    conn = connect(database_path)
    try:
        yield conn
    finally:
        conn.close()
