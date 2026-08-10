"""
Streamlit demo UI for the NetOps Agent — deployable free on Streamlit
Community Cloud (share.streamlit.io), directly from GitHub, no payment
tier required (unlike Gradio/Docker Spaces on Hugging Face, which now
require a paid plan to create on a personal account).

Functionally equivalent to ui/app.py, just built with Streamlit's widgets
instead of Gradio's.
"""
from __future__ import annotations

import json
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
import uvicorn

st.set_page_config(page_title="NetOps Agent — Portfolio Demo", page_icon="🛰️", layout="wide")


@st.cache_resource
def _start_mock_services():
    """Boots the two mock FastAPI services in-process, once per app
    session, so this is a single deployable Streamlit app with no
    separate services to manage."""
    from services.network_monitoring_api import app as network_app
    from services.ticketing_api import app as ticketing_app

    def _run(app, port):
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")

    threading.Thread(target=_run, args=(network_app, 8001), daemon=True).start()
    threading.Thread(target=_run, args=(ticketing_app, 8002), daemon=True).start()
    time.sleep(1.5)
    return True


_start_mock_services()

from agent.graph import run_incident  # noqa: E402  (import after services boot)

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

st.title("🛰️ NetOps Agent")
st.markdown(
    "Agentic incident triage & resolution assistant for telecom network operations. "
    "Built as a portfolio project "
    "demonstrates a LangGraph multi-agent flow with tool use (live telemetry + ticketing APIs), "
    "RAG retrieval over runbooks (ChromaDB), and structured evaluation/observability. "
    "Runs fully offline with a deterministic mock LLM by default."
)
st.markdown(
    "[GitHub repo](https://github.com/JoshilFernandes/netops-agent) &nbsp;·&nbsp; "
    "Built by Joshil Fernandes"
)

scenario = st.selectbox("Preset scenario", options=[""] + list(PRESET_SCENARIOS.keys()))

col1, col2 = st.columns(2)
with col1:
    node_id_input = st.text_input("Node ID (or pick a preset above)", value="")
with col2:
    alert_text_input = st.text_area("Alert text", value="", height=100)

if st.button("Run agent", type="primary"):
    if scenario and scenario in PRESET_SCENARIOS:
        preset = PRESET_SCENARIOS[scenario]
        node_id = preset["node_id"]
        alert_text = preset["text"]
    else:
        node_id = node_id_input
        alert_text = alert_text_input

    if not node_id.strip() or not alert_text.strip():
        st.warning("Provide both a node ID and alert text, or pick a preset scenario.")
    else:
        incident = {
            "incident_id": f"DEMO-{int(time.time())}",
            "node_id": node_id.strip(),
            "region": "demo",
            "raw_alert_text": alert_text.strip(),
        }
        with st.spinner("Running the agent..."):
            result = run_incident(incident)

        st.subheader("Triage + retrieval + diagnostics")
        st.markdown(f"**Category:** {result['triage']['category']}")
        st.markdown(f"**Severity:** {result['triage']['severity']}")
        st.markdown(f"**Rationale:** {result['triage']['rationale']}")

        st.markdown("**Live telemetry:**")
        st.json(result.get("telemetry", {}))

        st.markdown("**Retrieved runbook context:**")
        for d in result.get("retrieved_docs", []):
            st.markdown(f"- `{d['source']}` (score {d['score']})")

        st.subheader("Ticketing")
        if result.get("ticket_id"):
            st.success(f"Ticket opened: `{result['ticket_id']}`")
        else:
            st.info("No ticket opened — severity below the ticket-creation threshold, handled as informational.")

        st.subheader("Resolution")
        st.markdown("**Internal resolution summary:**")
        st.write(result["resolution_summary"])
        st.markdown("**Customer-facing message:**")
        st.write(result["customer_message"])