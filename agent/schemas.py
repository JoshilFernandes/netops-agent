"""Shared Pydantic schemas / typed state for the agent graph."""
from __future__ import annotations

from typing import Any, Optional, TypedDict

from pydantic import BaseModel, Field


class IncidentInput(BaseModel):
    incident_id: str
    node_id: str
    region: str
    raw_alert_text: str = Field(
        ..., description="Free-text alert as it would arrive from a monitoring system or customer report"
    )


class RetrievedDoc(BaseModel):
    source: str
    content: str
    score: float


class TriageResult(BaseModel):
    category: str
    severity: str
    rationale: str


class ToolCallRecord(BaseModel):
    tool: str
    input: dict
    output: dict


class IncidentResult(BaseModel):
    incident_id: str
    triage: TriageResult
    retrieved_docs: list[RetrievedDoc]
    tool_calls: list[ToolCallRecord]
    ticket_id: Optional[str]
    resolution_summary: str
    customer_message: str


class AgentState(TypedDict, total=False):
    """LangGraph shared state passed between nodes."""
    incident: dict          # IncidentInput as dict
    triage: dict             # TriageResult as dict
    retrieved_docs: list      # list[dict]
    telemetry: dict
    tool_calls: list          # list[dict]
    ticket_id: Optional[str]
    resolution_summary: str
    customer_message: str
    trace_id: str
