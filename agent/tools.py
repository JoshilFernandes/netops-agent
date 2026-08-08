"""
Agent tools: thin, typed wrappers around the mock backend APIs plus the
RAG retriever. These are the "hands" of the agent — every external side
effect (reading telemetry, writing a ticket, searching the KB) happens
through one of these functions, which keeps the graph nodes themselves
free of I/O details and easy to unit test in isolation.
"""
from __future__ import annotations

import httpx

from agent.config import settings
from agent.kb import query_kb


def get_node_telemetry(node_id: str) -> dict:
    """Tool: fetch live telemetry for a node from the network monitoring API."""
    resp = httpx.get(f"{settings.NETWORK_API_BASE}/telemetry/{node_id}", timeout=5)
    resp.raise_for_status()
    return resp.json()


def get_outage_map(region: str | None = None) -> dict:
    """Tool: fetch correlated outage map, optionally scoped to a region."""
    params = {"region": region} if region else {}
    resp = httpx.get(f"{settings.NETWORK_API_BASE}/outage-map", params=params, timeout=5)
    resp.raise_for_status()
    return resp.json()


def search_runbooks(query: str, k: int = 3) -> list[dict]:
    """Tool: semantic search over the runbook knowledge base (RAG retrieval)."""
    return query_kb(query, k=k)


def create_ticket(title: str, description: str, severity: str, category: str, node_id: str) -> dict:
    """Tool: open an incident ticket in the ticketing system."""
    resp = httpx.post(
        f"{settings.TICKETING_API_BASE}/tickets",
        json={
            "title": title,
            "description": description,
            "severity": severity,
            "category": category,
            "node_id": node_id,
        },
        timeout=5,
    )
    resp.raise_for_status()
    return resp.json()


def update_ticket(ticket_id: str, status: str | None = None, note: str | None = None) -> dict:
    """Tool: update ticket status / add a progress note."""
    resp = httpx.patch(
        f"{settings.TICKETING_API_BASE}/tickets/{ticket_id}",
        json={"status": status, "note": note},
        timeout=5,
    )
    resp.raise_for_status()
    return resp.json()


# Tool registry: makes it trivial to bind these as LangChain/LangGraph
# tool-calling functions, and gives evals a single place to enumerate
# "what can this agent actually do".
TOOL_REGISTRY = {
    "get_node_telemetry": get_node_telemetry,
    "get_outage_map": get_outage_map,
    "search_runbooks": search_runbooks,
    "create_ticket": create_ticket,
    "update_ticket": update_ticket,
}
