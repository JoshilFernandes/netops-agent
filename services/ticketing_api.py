"""
Mock Ticketing API.

Simulates a ServiceNow/Jira-style incident ticketing system. The agent uses
this as a tool to create and update tickets as it works an incident. State
is kept in-memory for the demo; swap the storage layer for a real ticketing
system's REST API in production without touching the agent code, since the
agent only depends on this module's function signatures.
"""
from __future__ import annotations

import itertools
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Ticketing API (mock)", version="1.0.0")

_ticket_id_counter = itertools.count(1001)
_tickets: dict[str, dict] = {}


class TicketCreateRequest(BaseModel):
    title: str
    description: str
    severity: str  # low | medium | high | critical
    category: str
    node_id: str | None = None


class TicketUpdateRequest(BaseModel):
    status: str | None = None
    note: str | None = None


class Ticket(BaseModel):
    ticket_id: str
    title: str
    description: str
    severity: str
    category: str
    node_id: str | None
    status: str
    created_at: str
    updates: list[dict]


@app.post("/tickets", response_model=Ticket)
def create_ticket(req: TicketCreateRequest) -> Ticket:
    ticket_id = f"NOC-{next(_ticket_id_counter)}"
    ticket = {
        "ticket_id": ticket_id,
        "title": req.title,
        "description": req.description,
        "severity": req.severity,
        "category": req.category,
        "node_id": req.node_id,
        "status": "open",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updates": [],
    }
    _tickets[ticket_id] = ticket
    return Ticket(**ticket)


@app.patch("/tickets/{ticket_id}", response_model=Ticket)
def update_ticket(ticket_id: str, req: TicketUpdateRequest) -> Ticket:
    ticket = _tickets.get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if req.status:
        ticket["status"] = req.status
    if req.note:
        ticket["updates"].append(
            {"timestamp": datetime.now(timezone.utc).isoformat(), "note": req.note}
        )
    return Ticket(**ticket)


@app.get("/tickets/{ticket_id}", response_model=Ticket)
def get_ticket(ticket_id: str) -> Ticket:
    ticket = _tickets.get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return Ticket(**ticket)


@app.get("/tickets", response_model=list[Ticket])
def list_tickets() -> list[Ticket]:
    return [Ticket(**t) for t in _tickets.values()]


@app.get("/health")
def health():
    return {"status": "ok", "service": "ticketing-api"}
