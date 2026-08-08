"""Unit tests for individual agent tools, run against the mock services.

These assume the mock services are running locally on the default ports
(see README for how to start them, or use `make test`).
"""
import httpx
import pytest

from agent.tools import get_node_telemetry, search_runbooks


def _services_up() -> bool:
    try:
        httpx.get("http://localhost:8001/health", timeout=1)
        httpx.get("http://localhost:8002/health", timeout=1)
        return True
    except Exception:
        return False


requires_services = pytest.mark.skipif(not _services_up(), reason="mock services not running")


@requires_services
def test_get_node_telemetry_fiber_scenario():
    telemetry = get_node_telemetry("node-fiber-cut-berlin-04")
    assert telemetry["status"] == "DOWN"
    assert telemetry["optical_rx_dbm"] < -40


def test_search_runbooks_returns_relevant_doc():
    results = search_runbooks("fiber cut optical signal loss", k=2)
    assert len(results) > 0
    assert any(r["source"] == "fiber_outage.md" for r in results)


def test_search_runbooks_dns_query():
    results = search_runbooks("customers cannot resolve websites NXDOMAIN", k=2)
    assert any(r["source"] == "dns_resolution_failure.md" for r in results)
