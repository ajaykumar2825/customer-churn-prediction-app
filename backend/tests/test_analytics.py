"""Analytics, model-performance and strategy endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_analytics_dashboard(client: TestClient) -> None:
    response = client.get("/api/v1/analytics")
    assert response.status_code == 200
    body = response.json()
    kpis = body["kpis"]
    assert kpis["total_customers"] >= 5000
    assert 0.0 <= kpis["churn_rate"] <= 1.0
    for key in [
        "total_customers",
        "active_customers",
        "churn_rate",
        "revenue_at_risk",
        "avg_satisfaction",
        "avg_monthly_charges",
        "high_risk_customers",
        "retention_score",
    ]:
        assert key in kpis
    assert body["risk_distribution"]
    assert body["recent_predictions"]


def test_revenue_risk(client: TestClient) -> None:
    response = client.get("/api/v1/revenue-risk")
    assert response.status_code == 200
    bundle = response.json()["bundle"]
    assert "revenue_at_risk" in bundle
    assert "clv" in bundle
    assert "retention_roi" in bundle
    assert "segments" in bundle


def test_segments(client: TestClient) -> None:
    response = client.get("/api/v1/segments")
    assert response.status_code == 200
    segments = response.json()["segments"]
    assert "contract" in segments


def test_model_metrics(client: TestClient) -> None:
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["model"]
    assert body["leaderboard"]
    assert "roc" in body["curves"]
    assert "confusion" in body
    assert "importance" in body


def test_feature_importance(client: TestClient) -> None:
    response = client.get("/api/v1/feature-importance")
    assert response.status_code == 200
    importance = response.json()["importance"]
    assert importance["shap"]["importances"]
    assert importance["permutation"]


def test_model_status(client: TestClient) -> None:
    response = client.get("/api/v1/model/status")
    assert response.status_code == 200
    assert response.json()["ready"] is True