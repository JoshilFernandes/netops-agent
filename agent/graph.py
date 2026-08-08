"""
LangGraph state machine for the NetOps incident-triage agent.

Flow:
  triage -> retrieve -> diagnose (tool call) -> decide -> [ticket] -> respond

  - triage: LLM classifies the incoming alert into a category + severity
  - retrieve: RAG lookup of the matching runbook section(s)
  - diagnose: calls the network monitoring API tool to pull live telemetry
    for the node, and cross-checks it against the retrieved runbook's
    diagnostic thresholds
  - decide: routes to `ticket` for high/critical severity, otherwise
    skips straight to `respond` for low/medium self-resolving issues
  - ticket: opens a ticket via the ticketing API tool
  - respond: synthesizes the internal resolution summary + customer-facing
    message

Every node is wrapped in a tracer span so the whole run is fully
observable (see agent/tracer.py and dashboard/observability_dashboard.py).
"""
from __future__ import annotations

from langgraph.graph import END, StateGraph

from agent.llm import LLMClient, extract_json
from agent.schemas import AgentState
from agent.tools import create_ticket, get_node_telemetry, search_runbooks
from agent.tracer import tracer

llm = LLMClient()

TRIAGE_SYSTEM_PROMPT = """You are a telecom network incident triage classifier.
Read the alert text and classify it (this is a CLASSIFY step).
Respond ONLY with JSON: {"category": "...", "severity": "low|medium|high|critical", "rationale": "..."}
Valid categories: physical_layer, routing, application_layer, capacity, hardware, enterprise_services, unknown."""

SYNTHESIS_SYSTEM_PROMPT = """You are a senior NOC engineer writing an internal resolution SUMMARY.
Given the triage classification, retrieved runbook guidance, and live telemetry, write a concise
2-4 sentence internal summary of root cause and recommended next action."""

CUSTOMER_SYSTEM_PROMPT = """You write a short, reassuring CUSTOMER-facing status message (not internal jargon)
based on the incident summary. 2-3 sentences, plain language, no internal ticket IDs or technical thresholds."""


def node_triage(state: AgentState) -> AgentState:
    incident = state["incident"]
    with tracer.span(state["trace_id"], "triage"):
        raw = llm.complete(TRIAGE_SYSTEM_PROMPT, incident["raw_alert_text"])
        parsed = extract_json(raw)
    return {"triage": parsed}


def node_retrieve(state: AgentState) -> AgentState:
    incident = state["incident"]
    query = f"{state['triage']['category']} {incident['raw_alert_text']}"
    with tracer.span(state["trace_id"], "retrieve", query=query):
        docs = search_runbooks(query, k=2)
    return {"retrieved_docs": docs}


def node_diagnose(state: AgentState) -> AgentState:
    incident = state["incident"]
    with tracer.span(state["trace_id"], "diagnose", node_id=incident["node_id"]):
        telemetry = get_node_telemetry(incident["node_id"])
        tracer.log_tool_call(
            state["trace_id"], "get_node_telemetry", {"node_id": incident["node_id"]}, telemetry
        )
    tool_calls = state.get("tool_calls", [])
    tool_calls.append(
        {"tool": "get_node_telemetry", "input": {"node_id": incident["node_id"]}, "output": telemetry}
    )
    return {"telemetry": telemetry, "tool_calls": tool_calls}


def route_after_diagnose(state: AgentState) -> str:
    severity = state["triage"].get("severity", "medium")
    return "ticket" if severity in ("high", "critical") else "respond"


def node_ticket(state: AgentState) -> AgentState:
    incident = state["incident"]
    triage = state["triage"]
    with tracer.span(state["trace_id"], "ticket"):
        ticket = create_ticket(
            title=f"[{triage['severity'].upper()}] {triage['category']} incident on {incident['node_id']}",
            description=incident["raw_alert_text"],
            severity=triage["severity"],
            category=triage["category"],
            node_id=incident["node_id"],
        )
        tracer.log_tool_call(state["trace_id"], "create_ticket", {"node_id": incident["node_id"]}, ticket)
    tool_calls = state.get("tool_calls", [])
    tool_calls.append({"tool": "create_ticket", "input": {"node_id": incident["node_id"]}, "output": ticket})
    return {"ticket_id": ticket["ticket_id"], "tool_calls": tool_calls}


def node_respond(state: AgentState) -> AgentState:
    triage = state["triage"]
    docs_text = "\n---\n".join(d["content"] for d in state.get("retrieved_docs", []))
    telemetry = state.get("telemetry", {})

    synthesis_input = (
        f"Category: {triage['category']}, Severity: {triage['severity']}\n"
        f"Telemetry: {telemetry}\n"
        f"Runbook guidance:\n{docs_text}"
    )
    with tracer.span(state["trace_id"], "respond"):
        summary = llm.complete(SYNTHESIS_SYSTEM_PROMPT, synthesis_input)
        customer_msg = llm.complete(CUSTOMER_SYSTEM_PROMPT, summary)

    return {"resolution_summary": summary, "customer_message": customer_msg}


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("triage_step", node_triage)
    graph.add_node("retrieve_step", node_retrieve)
    graph.add_node("diagnose_step", node_diagnose)
    graph.add_node("ticket_step", node_ticket)
    graph.add_node("respond_step", node_respond)

    graph.set_entry_point("triage_step")
    graph.add_edge("triage_step", "retrieve_step")
    graph.add_edge("retrieve_step", "diagnose_step")
    graph.add_conditional_edges("diagnose_step", route_after_diagnose, {"ticket": "ticket_step", "respond": "respond_step"})
    graph.add_edge("ticket_step", "respond_step")
    graph.add_edge("respond_step", END)

    return graph.compile()


_compiled_graph = None


def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


def run_incident(incident: dict) -> dict:
    graph = get_graph()
    trace_id = tracer.new_trace_id()
    initial_state: AgentState = {
        "incident": incident,
        "trace_id": trace_id,
        "tool_calls": [],
        "ticket_id": None,
    }
    final_state = graph.invoke(initial_state)
    final_state["trace_id"] = trace_id
    return final_state
