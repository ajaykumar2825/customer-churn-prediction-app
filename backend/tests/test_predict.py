"""Prediction endpoints: single, batch and explain."""

from __future__ import annotations

from fastapi.testclient import TestClient

from conftest import SAMPLE_HIGH_RISK, SAMPLE_LOW_RISK


def test_predict_high_risk(client: TestClient) -> None:
    response = client.post("/api/v1/predict", json=SAMPLE_HIGH_RISK)
    assert response.status_code == 200
    body = response.json()
    assert 0.0 <= body["probability"] <= 1.0
    assert body["risk_level"] in {"low", "medium", "high"}
    assert body["model"]
    assert body["threshold"]
    assert body["top_factors"]
    assert body["confidence"] >= 0.5


def test_predict_low_risk(client: TestClient) -> None:
    response = client.post("/api/v1/predict", json=SAMPLE_LOW_RISK)
    assert response.status_code == 200
    body = response.json()
    assert body["risk_level"].lower() in {"low", "medium"}
    assert body["predicted_churn"] is False


def test_predict_validation_error(client: TestClient) -> None:
    payload = dict(SAMPLE_HIGH_RISK, monthly_charges=-5)
    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 422


def test_predict_batch(client: TestClient) -> None:
    payload = {"customers": [SAMPLE_HIGH_RISK, SAMPLE_LOW_RISK]}
    response = client.post("/api/v1/predict/batch", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["count"] == 2
    assert len(body["predictions"]) == 2


def test_explain_endpoint(client: TestClient) -> None:
    response = client.post("/api/v1/explain", json=SAMPLE_HIGH_RISK)
    assert response.status_code == 200
    body = response.json()
    explanation = body["explanation"]
    assert "contributions" in explanation
    assert explanation["contributions"]