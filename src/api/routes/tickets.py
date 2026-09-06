"""Ticket endpoints - the human side of the queue."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from api.deps import get_db
from models.schemas import Ticket, TicketCreate, TicketStatus, TicketUpdate
from services import tickets as ticket_service

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get("", response_model=list[Ticket])
def list_tickets(
    status: TicketStatus | None = Query(None), conn=Depends(get_db)
) -> list[dict]:
    return ticket_service.list_tickets(conn, status=status)


@router.post("", response_model=Ticket, status_code=201)
def create_ticket(payload: TicketCreate, conn=Depends(get_db)) -> dict:
    return ticket_service.create_ticket(
        conn,
        subject=payload.subject,
        body=payload.body,
        reason=payload.reason,
        customer_email=payload.customer_email,
    )


@router.get("/{ticket_id}", response_model=Ticket)
def get_ticket(ticket_id: int, conn=Depends(get_db)) -> dict:
    ticket = ticket_service.get_ticket(conn, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found.")
    return ticket


@router.patch("/{ticket_id}", response_model=Ticket)
def update_ticket(
    ticket_id: int, payload: TicketUpdate, conn=Depends(get_db)
) -> dict:
    if ticket_service.get_ticket(conn, ticket_id) is None:
        raise HTTPException(status_code=404, detail="Ticket not found.")
    return ticket_service.update_status(conn, ticket_id, payload.status)
