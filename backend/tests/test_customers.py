"""Customer read endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_list_customers_paginated(client: TestClient) -> None:
    response = client.get("/api/v1/customers?page=1&page_size=5")
    assert response.status_code == 200
    body = response.json()
    assert body["page"] == 1
    assert body["page_size"] == 5
    assert len(body["items"]) == 5
    assert body["total"] >= 5000
    assert "churn_probability" in body["items"][0]


def test_filter_high_risk_sort(client: TestClient) -> None:
    response = client.get("/api/v1/customers?risk=high&sort_by=churn_probability&page_size=3")
    assert response.status_code == 200
    items = response.json()["items"]
    assert items
    for item in items:
        assert item["risk_level"] == "high"
        assert item["churn_probability"] >= 0.5


def test_search_customer(client: TestClient) -> None:
    response = client.get("/api/v1/customers?search=7590&sort_by=customer_id&ascending=true&page_size=5")
    assert response.status_code == 200
    items = response.json()["items"]
    assert items
    assert any("7590" in item["customer_id"] for item in items)


def test_customer_detail_and_not_found(client: TestClient) -> None:
    listing = client.get("/api/v1/customers?page_size=1").json()["items"][0]
    customer_id = listing["customer_id"]
    detail = client.get(f"/api/v1/customers/{customer_id}")
    assert detail.status_code == 200
    assert detail.json()["customer_id"] == customer_id

    missing = client.get("/api/v1/customers/nonexistent-12345")
    assert missing.status_code == 404


def test_customer_export_csv(client: TestClient) -> None:
    response = client.get("/api/v1/customers/export?risk=high")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert response.content.decode().startswith("customer_id")


def test_customer_explain(client: TestClient) -> None:
    listing = client.get("/api/v1/customers?page_size=1").json()["items"][0]
    response = client.get(f"/api/v1/customers/{listing['customer_id']}/explain")
    assert response.status_code == 200
    assert response.json()["explanation"] is not None