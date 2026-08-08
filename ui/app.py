"""
Gradio demo UI for the NetOps Agent — deployable as-is to Hugging Face
Spaces (consistent with the free-hosting approach used across this
portfolio: HF Spaces + Gradio, no paid infra required for a demo).

Lets a reviewer trigger a few preset incident scenarios (or type a free-
text alert) and see the full agent trace: triage -> retrieval -> live
telemetry -> routing decision -> ticket -> summary, without needing to
run curl or read code.
"""
from __future__ import annotations

import json
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import gradio as gr
import uvicorn

from agent.graph import run_incident

PRESET_SCENARIOS = {
    "🔴 Critical: Fiber cut in Berlin": {
        "node_id": "node-fiber-cut-berlin-04",
        "text": "Total signal loss reported on fiber segment, node shows DOWN, customers reporting complete outage in the area.",
    },
    "🟠 High: BGP flapping in Hannover": {
        "node_id": "node-bgp-flap-hannover-11",
        "text": "Router is repeatedly flapping its BGP session with a peer, intermittent packet loss reported by customers.",
    },
    "🟡 Medium: DNS resolution failures": {
        "node_id": "node-dns-resolver-01",
        "text": "Multiple customers report they cannot resolve certain websites, resolver logs show elevated NXDOMAIN rate.",
    },
    "🟡 Medium: Peak-hour congestion in Munich": {
        "node_id": "node-congestion-munich-02",
        "text": "Customers reporting slow speeds during peak hours, link utilization consistently above 90 percent.",
    },
    "🔴 Critical: Core router hardware failure": {
        "node_id": "node-hw-failure-duesseldorf-07",
        "text": "Core router stopped responding to SNMP polling entirely, heartbeat lost, power supply status unknown.",
    },
    "🟡 Medium: Enterprise VPN tunnel dropping": {
        "node_id": "node-vpn-issue-guetersloh-03",
        "text": "Enterprise customer's site-to-site VPN tunnel keeps renegotiating and dropping, IKE phase failing.",
    },
}


def _start_mock_services_in_background():
    """Boots the two mock FastAPI services in-process so this demo is a
    single deployable Gradio app with no separate services to manage."""
    from services.network_monitoring_api import app as network_app
    from services.ticketing_api import app as ticketing_app

    def _run(app, port):
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")

    threading.Thread(target=_run, args=(network_app, 8001), daemon=True).start()
    threading.Thread(target=_run, args=(ticketing_app, 8002), daemon=True).start()
    time.sleep(1.5)


def process_incident(scenario_name: str, node_id: str, alert_text: str):
    if scenario_name and scenario_name in PRESET_SCENARIOS:
        preset = PRESET_SCENARIOS[scenario_name]
        node_id = preset["node_id"]
        alert_text = preset["text"]

    if not alert_text.strip() or not node_id.strip():
        return "⚠️ Provide both a node ID and alert text, or pick a preset scenario.", "", ""

    incident = {
        "incident_id": f"DEMO-{int(time.time())}",
        "node_id": node_id.strip(),
        "region": "demo",
        "raw_alert_text": alert_text.strip(),
    }
    result = run_incident(incident)

    triage_md = (
        f"**Category:** {result['triage']['category']}  \n"
        f"**Severity:** {result['triage']['severity']}  \n"
        f"**Rationale:** {result['triage']['rationale']}  \n\n"
        f"**Live telemetry:**\n```json\n{json.dumps(result.get('telemetry', {}), indent=2)}\n```\n\n"
        f"**Retrieved runbook context:**\n" +
        "\n".join(f"- `{d['source']}` (score {d['score']})" for d in result.get("retrieved_docs", []))
    )

    ticket_md = (
        f"**Ticket opened:** `{result['ticket_id']}`" if result.get("ticket_id")
        else "_No ticket opened — severity below the ticket-creation threshold, handled as informational._"
    )

    response_md = (
        f"**Internal resolution summary:**\n{result['resolution_summary']}\n\n"
        f"**Customer-facing message:**\n{result['customer_message']}"
    )

    return triage_md, ticket_md, response_md


with gr.Blocks(title="NetOps Agent — Reply Portfolio Demo") as demo:
    gr.Markdown(
        "# 🛰️ NetOps Agent\n"
        "Agentic incident triage & resolution assistant for telecom network operations.\n\n"
        "Built as a portfolio project for the **Agentic Software Engineer** role at Reply — "
        "demonstrates a LangGraph multi-agent flow with tool use (live telemetry + ticketing APIs), "
        "RAG retrieval over runbooks (ChromaDB), and structured evaluation/observability. "
        "Runs fully offline with a deterministic mock LLM by default; set `LLM_PROVIDER=anthropic` "
        "with an API key for live Claude reasoning."
    )
    with gr.Row():
        with gr.Column():
            scenario = gr.Dropdown(
                choices=list(PRESET_SCENARIOS.keys()), label="Preset scenario (or fill in your own below)"
            )
            node_id = gr.Textbox(label="Node ID", placeholder="e.g. node-fiber-cut-berlin-04")
            alert_text = gr.Textbox(label="Alert text", lines=3, placeholder="Describe the incident...")
            submit = gr.Button("Run agent", variant="primary")
        with gr.Column():
            triage_out = gr.Markdown(label="Triage + Retrieval + Diagnostics")
            ticket_out = gr.Markdown(label="Ticketing")
            response_out = gr.Markdown(label="Resolution")

    submit.click(process_incident, inputs=[scenario, node_id, alert_text], outputs=[triage_out, ticket_out, response_out])

if __name__ == "__main__":
    _start_mock_services_in_background()
    demo.launch()
