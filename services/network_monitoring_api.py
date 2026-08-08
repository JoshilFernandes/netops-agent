"""
Mock Network Monitoring API.

Simulates a telecom NOC monitoring system (e.g. what a real Reply telecom
client such as a network operator would expose internally). The agent calls
this as a *tool* to fetch live telemetry for a given node/incident.

In a real engagement this would be a thin client wrapping something like
SolarWinds, a vendor NMS, or an internal gRPC/REST telemetry service. Here
we simulate deterministic-but-varied telemetry keyed by node_id so the
agent's reasoning can be evaluated reproducibly.
"""
from __future__ import annotations

import hashlib
import random
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Network Monitoring API (mock)", version="1.0.0")


class NodeTelemetry(BaseModel):
    node_id: str
    status: str
    optical_rx_dbm: float
    bgp_flap_count_15m: int
    link_utilization_pct: float
    last_heartbeat: str
    temperature_c: float
    tunnel_state: str


def _seeded_rng(node_id: str) -> random.Random:
    seed = int(hashlib.sha256(node_id.encode()).hexdigest(), 16) % (10**8)
    return random.Random(seed)


# Scenario overrides let the eval suite / demo force specific fault types
# for deterministic testing, while unseen node_ids get plausible random data.
SCENARIO_OVERRIDES: dict[str, dict] = {
    "node-fiber-cut-berlin-04": {
        "status": "DOWN",
        "optical_rx_dbm": -42.5,
        "bgp_flap_count_15m": 0,
        "link_utilization_pct": 0.0,
        "temperature_c": 24.1,
        "tunnel_state": "n/a",
    },
    "node-bgp-flap-hannover-11": {
        "status": "DEGRADED",
        "optical_rx_dbm": -12.0,
        "bgp_flap_count_15m": 9,
        "link_utilization_pct": 41.0,
        "temperature_c": 26.3,
        "tunnel_state": "n/a",
    },
    "node-congestion-munich-02": {
        "status": "UP",
        "optical_rx_dbm": -11.0,
        "bgp_flap_count_15m": 0,
        "link_utilization_pct": 96.4,
        "temperature_c": 29.8,
        "tunnel_state": "n/a",
    },
    "node-hw-failure-duesseldorf-07": {
        "status": "UNREACHABLE",
        "optical_rx_dbm": -99.0,
        "bgp_flap_count_15m": 0,
        "link_utilization_pct": 0.0,
        "temperature_c": 0.0,
        "tunnel_state": "n/a",
    },
    "node-vpn-issue-guetersloh-03": {
        "status": "UP",
        "optical_rx_dbm": -10.5,
        "bgp_flap_count_15m": 0,
        "link_utilization_pct": 22.0,
        "temperature_c": 25.0,
        "tunnel_state": "IKE_RENEGOTIATING",
    },
}


@app.get("/telemetry/{node_id}", response_model=NodeTelemetry)
def get_telemetry(node_id: str) -> NodeTelemetry:
    rng = _seeded_rng(node_id)
    override = SCENARIO_OVERRIDES.get(node_id, {})

    data = {
        "node_id": node_id,
        "status": override.get("status", rng.choice(["UP", "UP", "UP", "DEGRADED"])),
        "optical_rx_dbm": override.get("optical_rx_dbm", round(rng.uniform(-14, -8), 1)),
        "bgp_flap_count_15m": override.get("bgp_flap_count_15m", rng.choice([0, 0, 0, 1])),
        "link_utilization_pct": override.get("link_utilization_pct", round(rng.uniform(20, 60), 1)),
        "last_heartbeat": (datetime.now(timezone.utc) - timedelta(seconds=rng.randint(1, 30))).isoformat(),
        "temperature_c": override.get("temperature_c", round(rng.uniform(22, 30), 1)),
        "tunnel_state": override.get("tunnel_state", "ESTABLISHED"),
    }
    return NodeTelemetry(**data)


@app.get("/outage-map")
def get_outage_map(region: str | None = None):
    """Returns currently correlated outages, optionally filtered by region."""
    outages = [
        {"region": "Berlin", "affected_nodes": 4, "root_node": "node-fiber-cut-berlin-04"},
        {"region": "Hannover", "affected_nodes": 1, "root_node": "node-bgp-flap-hannover-11"},
    ]
    if region:
        outages = [o for o in outages if o["region"].lower() == region.lower()]
    return {"outages": outages}


@app.get("/health")
def health():
    return {"status": "ok", "service": "network-monitoring-api"}
