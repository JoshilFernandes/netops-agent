"""API-level tests for the orchestrator and mock backend services using
FastAPI's TestClient (no real network calls / no servers needed to run
these particular tests)."""
from fastapi.testclient import TestClient

from services.network_monitoring_api import app as network_app
from services.ticketing_api import app as ticketing_app


def test_network_api_health():
    client = TestClient(network_app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_network_api_telemetry_shape():
    client = TestClient(network_app)
    resp = client.get("/telemetry/some-random-node")
    assert resp.status_code == 200
    body = resp.json()
    assert "status" in body and "optical_rx_dbm" in body


def test_ticketing_api_create_and_fetch():
    client = TestClient(ticketing_app)
    create_resp = client.post(
        "/tickets",
        json={
            "title": "Test incident",
            "description": "unit test",
            "severity": "high",
            "category": "routing",
            "node_id": "node-x",
        },
    )
    assert create_resp.status_code == 200
    ticket_id = create_resp.json()["ticket_id"]

    get_resp = client.get(f"/tickets/{ticket_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["status"] == "open"


def test_ticketing_api_update():
    client = TestClient(ticketing_app)
    create_resp = client.post(
        "/tickets",
        json={"title": "t", "description": "d", "severity": "low", "category": "capacity", "node_id": "n"},
    )
    ticket_id = create_resp.json()["ticket_id"]

    update_resp = client.patch(f"/tickets/{ticket_id}", json={"status": "resolved", "note": "fixed"})
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "resolved"
    assert len(update_resp.json()["updates"]) == 1
