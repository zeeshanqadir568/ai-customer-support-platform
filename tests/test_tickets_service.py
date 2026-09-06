"""Tests for the ticket persistence layer."""

from services import tickets


def test_create_and_get(conn):
    created = tickets.create_ticket(
        conn,
        subject="Refund review",
        body="Customer wants a refund on a high-value order.",
        reason="refund_review",
        customer_email="ada@example.com",
    )
    assert created["id"] > 0
    assert created["status"] == "open"

    fetched = tickets.get_ticket(conn, created["id"])
    assert fetched["subject"] == "Refund review"


def test_list_and_filter_by_status(conn):
    a = tickets.create_ticket(conn, subject="A", body="a", reason="x")
    tickets.create_ticket(conn, subject="B", body="b", reason="y")
    tickets.update_status(conn, a["id"], "resolved")

    assert len(tickets.list_tickets(conn)) == 2
    assert [t["subject"] for t in tickets.list_tickets(conn, status="open")] == ["B"]
    assert [t["subject"] for t in tickets.list_tickets(conn, status="resolved")] == ["A"]


def test_get_missing_returns_none(conn):
    assert tickets.get_ticket(conn, 424242) is None
