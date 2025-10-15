import pytest
from fastapi.testclient import TestClient

from services.orchestrator.main import app as orch_app
from services.api.main import app as ops_app


def test_health_ok():
    client = TestClient(orch_app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_registry_endpoint():
    client = TestClient(ops_app)
    r = client.get("/registry")
    assert r.status_code == 200
    body = r.json()
    assert "entries" in body
