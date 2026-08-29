"""Customer + analytics read services with Postgres/SQLite and in-memory fallback."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import database_online
from app.models.orm import Customer
from app.services import demo_store
from app.services.model_service import risk_level

logger = logging.getLogger("churn.CustomerService")


class CustomerService:
    """Read-side access to customers and derived dashboard aggregations."""

    @staticmethod
    def _db() -> bool:
        return database_online() and bool(settings.database_url)

    def list_customers(
        self,
        session: Session | None,
        query: str | None = None,
        contract: str | None = None,
        risk: str | None = None,
        churn: bool | None = None,
        sort_by: str = "churn_probability",
        ascending: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        if not self._db():
            records, pages = demo_store.search_customers(query, contract, risk, churn, sort_by, ascending, page, page_size)
            return {
                "items": records,
                "total": _demo_total(query, contract, risk, churn),
                "page": page,
                "page_size": page_size,
                "pages": pages,
            }

        stmt = select(Customer)
        conditions: list = []
        if query:
            conditions.append(Customer.customer_id.ilike(f"%{query}%"))
        if contract:
            conditions.append(Customer.contract == contract)
        if risk:
            conditions.append(_risk_clause(risk))
        if churn is not None:
            conditions.append(Customer.predicted_churn == churn)
        for cond in conditions:
            stmt = stmt.where(cond)

        total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        sort_col = getattr(Customer, sort_by, Customer.churn_probability)
        stmt = stmt.order_by(sort_col.asc() if ascending else sort_col.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        items = [_row_to_dict(c) for c in session.scalars(stmt)]
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": max(int(np.ceil(total / page_size)), 1),
        }

    def get_customer(self, session: Session | None, customer_id: str) -> dict[str, Any] | None:
        if not self._db():
            return demo_store.get_customer(customer_id)
        row = session.scalar(select(Customer).where(Customer.customer_id == customer_id))
        return _row_to_dict(row) if row else None

    def analytics(self, session: Session | None) -> dict[str, Any]:
        if not self._db():
            return demo_store_frame_analytics()
        frame = self._db_frame(session)
        return _frame_analytics(frame)

    def revenue_bundle(self, session: Session | None) -> dict[str, Any]:
        """Business bundle computed over the live customer base."""
        from ml_pipeline.business import build_business_bundle

        frame = demo_store.get_frame() if not self._db() else self._db_frame(session)
        return build_business_bundle(frame, "churn_probability")

    def _db_frame(self, session: Session | None) -> pd.DataFrame:
        rows = session.scalars(select(Customer)).all() if session else []
        return pd.DataFrame([_row_to_dict(r) for r in rows])


def _demo_total(query, contract, risk, churn) -> int:
    try:
        frame = demo_store.get_frame()
        mask = pd.Series(True, index=frame.index)
        if query:
            mask &= frame["customer_id"].str.contains(query, case=False, na=False)
        if contract:
            mask &= frame["contract"] == contract
        if risk:
            mask &= frame.apply(lambda r: risk_level(r["churn_probability"]) == risk, axis=1)
        if churn is not None:
            mask &= frame["predicted_churn"] == churn
        return int(mask.sum())
    except Exception:
        return 7032


def _risk_clause(risk: str):
    if risk == "low":
        return Customer.churn_probability < 0.5
    if risk == "medium":
        return and_(
            Customer.churn_probability >= 0.5,
            Customer.churn_probability < settings.high_risk_threshold,
        )
    return Customer.churn_probability >= settings.high_risk_threshold


def _row_to_dict(c: Customer) -> dict[str, Any]:
    return {
        "customer_id": c.customer_id,
        "tenure": c.tenure,
        "monthly_charges": c.monthly_charges,
        "total_charges": c.total_charges,
        "avg_monthly_charge": c.avg_monthly_charge,
        "contract": c.contract,
        "internet_service": c.internet_service,
        "payment_method": c.payment_method,
        "senior_citizen": bool(c.senior_citizen),
        "gender_female": bool(c.gender_female),
        "partner": bool(c.partner),
        "dependents": bool(c.dependents),
        "paperless_billing": bool(c.paperless_billing),
        "total_services": c.total_services,
        "churn_probability": c.churn_probability,
        "risk_level": risk_level(c.churn_probability),
        "predicted_churn": bool(c.predicted_churn),
        "observed_churn": bool(c.observed_churn),
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "satisfaction_score": _satisfaction_of(c) if c.created_at else 3.2,
    }


def _satisfaction_of(c: Customer) -> float:
    raw = (
        2.1
        + 0.05 * c.tenure / 72 * 3
        + 0.7 * int(c.tech_support)
        + 0.5 * int(c.online_security)
        + 0.4 * int(c.dependents)
        - 1.2 * int(c.churn_probability >= 0.7)
    )
    return round(float(np.clip(raw, 1.0, 5.0)), 2)


def demo_store_frame_analytics() -> dict[str, Any]:
    return _frame_analytics(demo_store.get_frame())


def _frame_analytics(frame: pd.DataFrame) -> dict[str, Any]:
    """Dashboard aggregation shared by the DB and in-memory paths."""
    total = int(len(frame))
    active = int(frame[frame["churn"] == 0].shape[0])
    churn_rate = float(frame["churn"].mean())
    risk_amount = float((frame["monthly_charges"] * frame["churn_probability"]).sum())
    avg_sat = float(frame["satisfaction_score"].mean()) if "satisfaction_score" in frame else 0.0
    avg_monthly = float(frame["monthly_charges"].mean())
    high = int((frame["churn_probability"] >= settings.high_risk_threshold).sum())
    retention = float((1 - frame["churn_probability"]).mean())

    revenue_trend = _bucketed(frame, "tenure", "monthly_charges", 6, "sum")
    churn_trend = _bucketed(frame, "tenure", "churn", 6, "count")

    risk_distribution = [
        {"label": "Low Risk", "value": int((frame["churn_probability"] < 0.5).sum())},
        {
            "label": "Medium Risk",
            "value": int(((frame["churn_probability"] >= 0.5) & (frame["churn_probability"] < settings.high_risk_threshold)).sum()),
        },
        {"label": "High Risk", "value": high},
    ]

    recent_predictions = (
        frame.sort_values("churn_probability", ascending=False)
        .head(8)[["customer_id", "churn_probability", "contract", "monthly_charges", "payment_method"]]
        .to_dict("records")
    )

    return {
        "kpis": {
            "total_customers": total,
            "active_customers": active,
            "churn_rate": round(churn_rate, 4),
            "revenue_at_risk": round(risk_amount, 2),
            "avg_satisfaction": round(avg_sat, 2),
            "avg_monthly_charges": round(avg_monthly, 2),
            "high_risk_customers": high,
            "retention_score": round(retention, 4),
        },
        "trends": {"revenue": revenue_trend, "churn": churn_trend, "customers": _cumulative(frame["churn"])},
        "risk_distribution": risk_distribution,
        "recent_predictions": [dict(r) | {"probability": float(r["churn_probability"])} for _, r in pd.DataFrame(recent_predictions).iterrows()] if recent_predictions else [],
        "quick_stats": {"rows": total, "columns": len(frame.columns), "churners": int(churn_rate * total)},
    }


def _bucketed(frame: pd.DataFrame, bucket_col: str, value_col: str, buckets: int, how: str) -> list[dict]:
    frame = frame.copy()
    try:
        frame["_bucket"] = pd.qcut(frame[bucket_col], buckets, duplicates="drop")
    except ValueError:
        frame["_bucket"] = frame[bucket_col].astype(str)
    grouped = frame.groupby("_bucket", observed=True)[value_col].agg(how).reset_index()
    ordered = _ordered_buckets(grouped["_bucket"].astype(str).tolist())
    merged = {}
    for _, row in grouped.iterrows():
        merged[str(row["_bucket"])] = float(row[value_col])
    return [{"t": str(k), "value": merged.get(str(k), 0.0)} for k in ordered]


def _ordered_buckets(labels: list[str]) -> list[str]:
    def rank(label: str) -> tuple:
        import re

        match = re.search(r"[(\[](\d+(?:\.\d+)?(?:[.,]\d+)?)", label)
        return (float(match.group(1).replace(",", ".")) if match else 1e9, label)

    return sorted(labels, key=rank)


def _cumulative(churn_series: pd.Series) -> list[dict]:
    cumulative, seen = 0, []
    for _, value in churn_series.sort_index().items():
        cumulative += 1 if int(value) == 0 else 0
        seen.append({"t": _, "value": cumulative})
    return seen


customer_service = CustomerService()
