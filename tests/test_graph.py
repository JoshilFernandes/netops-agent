"""Integration tests for the full LangGraph incident flow (mock LLM mode).

Requires the mock backend services to be running (see README / Makefile).
"""
import httpx
import pytest

from agent.graph import run_incident


def _services_up() -> bool:
    try:
        httpx.get("http://localhost:8001/health", timeout=1)
        httpx.get("http://localhost:8002/health", timeout=1)
        return True
    except Exception:
        return False


requires_services = pytest.mark.skipif(not _services_up(), reason="mock services not running")


@requires_services
def test_critical_incident_opens_ticket():
    incident = {
        "incident_id": "TEST-1",
        "node_id": "node-fiber-cut-berlin-04",
        "region": "Berlin",
        "raw_alert_text": "Total signal loss on fiber segment, node DOWN, customers report full outage.",
    }
    result = run_incident(incident)

    assert result["triage"]["category"] == "physical_layer"
    assert result["triage"]["severity"] == "critical"
    assert result["ticket_id"] is not None
    assert any(d["source"] == "fiber_outage.md" for d in result["retrieved_docs"])
    assert result["telemetry"]["status"] == "DOWN"


@requires_services
def test_medium_incident_skips_ticket():
    incident = {
        "incident_id": "TEST-2",
        "node_id": "node-congestion-munich-02",
        "region": "Munich",
        "raw_alert_text": "Customers reporting slow speeds during peak hours, utilization above 90 percent.",
    }
    result = run_incident(incident)

    assert result["triage"]["severity"] == "medium"
    assert result["ticket_id"] is None
