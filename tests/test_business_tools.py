"""Unit tests for the read-only business lookups and refund policy."""

from services import business


def test_lookup_customer_found_and_case_insensitive(conn):
    assert business.lookup_customer(conn, "ada@example.com")["name"] == "Ada Lovelace"
    assert business.lookup_customer(conn, "  ADA@example.com ")["plan"] == "pro"


def test_lookup_customer_missing(conn):
    assert business.lookup_customer(conn, "nobody@example.com") is None


def test_lookup_order_by_id(conn):
    res = business.lookup_order(conn, order_id="ord-1001")
    assert res["found"] is True
    assert res["order"]["item"] == "Wireless keyboard"


def test_lookup_order_by_id_missing(conn):
    assert business.lookup_order(conn, order_id="ORD-9999")["found"] is False


def test_lookup_order_by_email_lists_all(conn):
    res = business.lookup_order(conn, email="ada@example.com")
    assert res["found"] is True
    assert {o["id"] for o in res["orders"]} == {"ORD-1001", "ORD-1002"}


def test_lookup_order_needs_an_argument(conn):
    assert business.lookup_order(conn)["found"] is False


def test_refund_eligible_within_window(conn):
    res = business.check_refund_eligibility(conn, "ORD-1001")
    assert res["eligible"] is True
    assert res["amount"] == 79.0


def test_refund_rejected_not_delivered(conn):
    res = business.check_refund_eligibility(conn, "ORD-1002")
    assert res["eligible"] is False
    assert "not delivered" in res["reason"]


def test_refund_rejected_outside_window(conn):
    res = business.check_refund_eligibility(conn, "ORD-1003")
    assert res["eligible"] is False
    assert "window" in res["reason"]


def test_refund_rejected_already_refunded(conn):
    res = business.check_refund_eligibility(conn, "ORD-1004")
    assert res["eligible"] is False
    assert "already refunded" in res["reason"]


def test_refund_unknown_order(conn):
    assert business.check_refund_eligibility(conn, "ORD-0000")["eligible"] is False
