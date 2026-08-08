"""
Orchestrator API: the public-facing entrypoint that wraps the LangGraph
agent as a REST service. This is what a Delivery Squad would expose to a
customer-facing chat UI, a Slack bot, or an internal ticketing integration.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, HTTPException

from agent.graph import run_incident
from agent.schemas import IncidentInput

app = FastAPI(title="NetOps Agent Orchestrator", version="1.0.0")


@app.post("/incident")
def handle_incident(incident: IncidentInput):
    try:
        result = run_incident(incident.model_dump())
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e)) from e
    return result


@app.get("/health")
def health():
    return {"status": "ok", "service": "orchestrator"}
