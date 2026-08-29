"""Customer read endpoints: list, profile, CSV export and per-customer explain."""

from __future__ import annotations

import csv
import io
from typing import Literal

from fastapi import APIRouter, Depends, Header, Query, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.schemas.analytics import CustomerOut, CustomersPage
from app.services.customer_service import customer_service
from app.services.model_service import model_service

router = APIRouter(tags=["customers"])


@router.get("/customers", response_model=CustomersPage)
def list_customers(
    session: Session = Depends(get_db),
    search: str | None = None,
    contract: str | None = Query(default=None, pattern="^(Month-to-month|One year|Two year)$"),
    risk: Literal["low", "medium", "high"] | None = None,
    churn: bool | None = None,
    sort_by: str = "churn_probability",
    ascending: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
) -> dict:
    """Search, filter, sort and paginate the customer base."""
    return customer_service.list_customers(
        session=session,
        query=search,
        contract=contract,
        risk=risk,
        churn=churn,
        sort_by=sort_by,
        ascending=ascending,
        page=page,
        page_size=page_size,
    )


@router.get("/customers/export", response_class=Response)
def export_customers(
    session: Session = Depends(get_db),
    search: str | None = None,
    risk: Literal["low", "medium", "high"] | None = None,
) -> Response:
    """Download the current filtered view of customers as CSV."""
    result = customer_service.list_customers(
        session=session,
        query=search,
        risk=risk,
        page=1,
        page_size=10_000,
    )
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    items = result["items"]
    if items:
        writer.writerow(list(items[0].keys()))
        for item in items:
            writer.writerow(list(item.values()))
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="customers.csv"'},
    )


@router.get("/customers/{customer_id}", response_model=CustomerOut)
def customer_detail(customer_id: str, session: Session = Depends(get_db)) -> dict:
    """Full profile of one customer."""
    customer = customer_service.get_customer(session, customer_id)
    if customer is None:
        raise NotFoundError("customer", customer_id)
    return customer


@router.get("/customer/{customer_id}", response_model=CustomerOut, include_in_schema=False)
def customer_detail_alias(customer_id: str, session: Session = Depends(get_db)) -> dict:
    """Backwards-compatible alias: ``/customer/{id}``."""
    return customer_detail(customer_id, session)


@router.get("/customers/{customer_id}/explain")
def customer_explain(
    customer_id: str,
    session: Session = Depends(get_db),
    x_forwarded_for: str | None = Header(default=None),
) -> dict:
    """SHAP explanation for a stored customer."""
    del session, x_forwarded_for
    customer = customer_service.get_customer(None, customer_id)
    if customer is None:
        raise NotFoundError("customer", customer_id)
    explanation = model_service.explain_input(customer)
    return {
        "customer_id": customer_id,
        "probability": customer["churn_probability"],
        "risk_level": customer["risk_level"],
        "explanation": explanation or {"error": "no explanation available"},
    }
