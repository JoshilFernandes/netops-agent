"""
Streamlit observability dashboard.

Reads the structured JSONL trace log written by agent/tracer.py and
visualizes per-node latency, tool-call volume, and error rate — the kind
of lightweight, homegrown observability the JD asks for explicitly
("Observability-Komponenten für LLM-basierte Funktionen"). In a real
Reply engagement this would likely be replaced/augmented with LangSmith
or an OpenTelemetry exporter into the client's existing APM stack; this
demonstrates the same underlying concepts (structured traces, span
timing, tool-call auditing) without requiring a paid third-party service.

Run with: streamlit run dashboard/observability_dashboard.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st

from agent.config import settings

st.set_page_config(page_title="NetOps Agent — Observability", layout="wide")
st.title("🛰️ NetOps Agent — Observability Dashboard")

trace_path = Path(settings.TRACE_LOG_PATH)

if not trace_path.exists():
    st.warning(
        f"No trace log found at `{trace_path}`. Run an incident through the agent "
        "(via the API, the Gradio demo, or `python evals/run_evals.py`) to generate traces."
    )
    st.stop()

events = [json.loads(line) for line in trace_path.read_text().splitlines() if line.strip()]
df = pd.DataFrame(events)

node_spans = df[df["node"].notna()] if "node" in df.columns else pd.DataFrame()
tool_calls = df[df.get("event") == "tool_call"] if "event" in df.columns else pd.DataFrame()

col1, col2, col3 = st.columns(3)
col1.metric("Traced runs", df["trace_id"].nunique() if "trace_id" in df.columns else 0)
col2.metric("Node spans recorded", len(node_spans))
col3.metric("Tool calls recorded", len(tool_calls))

st.subheader("Latency per node (ms)")
if not node_spans.empty:
    latency_summary = node_spans.groupby("node")["duration_ms"].agg(["mean", "max", "count"]).round(2)
    st.bar_chart(latency_summary["mean"])
    st.dataframe(latency_summary)
else:
    st.info("No node spans yet.")

st.subheader("Tool call volume")
if not tool_calls.empty:
    st.bar_chart(tool_calls["tool"].value_counts())
else:
    st.info("No tool calls recorded yet.")

st.subheader("Errors")
errors = node_spans[node_spans["error"].notna()] if "error" in node_spans.columns else pd.DataFrame()
if not errors.empty:
    st.error(f"{len(errors)} node(s) raised errors")
    st.dataframe(errors[["trace_id", "node", "error"]])
else:
    st.success("No errors recorded in trace log.")

st.subheader("Raw trace log (most recent 50 events)")
st.dataframe(df.tail(50))
