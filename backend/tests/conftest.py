"""Shared fixtures: application under test with the deployed model loaded."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core import bootstrap
from app.main import app
from app.services.model_service import model_service


@pytest.fixture(scope="session", autouse=True)
def _environment() -> None:
    bootstrap.ensure_repo_importable()


@pytest.fixture(scope="session")
def client() -> TestClient:
    model_service.load()
    assert model_service.ready, "model artefacts must be trained before running API tests"
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def vm() -> None:
    """Alias to guarantee model load before tests run."""
    return None


SAMPLE_HIGH_RISK = {
    "customer_id": "sample-1001",
    "tenure": 2,
    "monthly_charges": 95.0,
    "total_charges": 190.0,
    "avg_monthly_charge": 95.0,
    "senior_citizen": True,
    "gender_female": True,
    "paperless_billing": True,
    "partner": False,
    "dependents": False,
    "multi_line": True,
    "online_security": False,
    "online_backup": False,
    "device_protection": False,
    "tech_support": False,
    "streaming_tv": True,
    "streaming_movies": True,
    "total_services": 4,
    "internet_service": "Fiber optic",
    "contract": "Month-to-month",
    "payment_method": "Electronic check",
}

SAMPLE_LOW_RISK = {
    "customer_id": "sample-1002",
    "tenure": 40,
    "monthly_charges": 60.0,
    "total_charges": 2400.0,
    "avg_monthly_charge": 60.0,
    "senior_citizen": False,
    "gender_female": True,
    "paperless_billing": False,
    "partner": True,
    "dependents": True,
    "multi_line": False,
    "online_security": True,
    "online_backup": True,
    "device_protection": True,
    "tech_support": True,
    "streaming_tv": False,
    "streaming_movies": False,
    "total_services": 5,
    "internet_service": "DSL",
    "contract": "Two year",
    "payment_method": "Bank transfer (automatic)",
}