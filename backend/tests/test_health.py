"""System endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["model"] != "not_loaded"


def test_readiness(client: TestClient) -> None:
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    assert response.json()["ready"] is True


def test_metrics_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/ops/metrics")
    assert response.status_code == 200
    assert response.json()["model"]["loaded"] is True


def test_model_performance_metrics(client: TestClient) -> None:
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    assert "meta" in response.json()


def test_docs(client: TestClient) -> None:
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200