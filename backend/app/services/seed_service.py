"""Database seeding: ingests the demo predictions into Postgres/SQLite.

The seed writes the real 7k+ customer base (features + live model output)
into ``customers``, a prediction-history trail with timestamps spread over
the past 90 days, a demo platform user and a sample audit trail.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.orm import AuditLog, Customer, Prediction, User
from app.services import demo_store
from app.services.model_service import model_service, risk_level


def _spread_date(days_ago_range: tuple[int, int]) -> datetime:
    days = random.randint(*days_ago_range)
    return datetime.now(timezone.utc) - timedelta(days=days)


def seed_database(session: Session | None = None, clear: bool = True) -> dict[str, int]:
    """Idempotent-cum-progressive seed.

    ``clear`` refreshes the customers table which is cheap at 7k rows.
    Prediction history is append-only across runs.
    """
    session = session or SessionLocal()
    frame = demo_store.get_frame()
    customer_count = 0

    if clear:
        session.query(Customer).delete()

    for _, row in frame.iterrows():
        session.add(
            Customer(
                customer_id=str(row["customer_id"]),
                senior_citizen=bool(row["senior_citizen"]),
                gender_female=bool(row["gender_female"]),
                partner=bool(row["partner"]),
                dependents=bool(row["dependents"]),
                tenure=int(row["tenure"]),
                monthly_charges=float(row["monthly_charges"]),
                total_charges=float(row["total_charges"]),
                avg_monthly_charge=float(row["avg_monthly_charge"]),
                paperless_billing=bool(row["paperless_billing"]),
                multi_line=bool(row["multi_line"]),
                online_security=bool(row["online_security"]),
                online_backup=bool(row["online_backup"]),
                device_protection=bool(row["device_protection"]),
                tech_support=bool(row["tech_support"]),
                streaming_tv=bool(row["streaming_tv"]),
                streaming_movies=bool(row["streaming_movies"]),
                total_services=int(row["total_services"]),
                internet_service=str(row["internet_service"]),
                contract=str(row["contract"]),
                payment_method=str(row["payment_method"]),
                churn_probability=float(row["churn_probability"]),
                risk_level=risk_level(float(row["churn_probability"])),
                predicted_churn=bool(row["predicted_churn"]),
                observed_churn=bool(row["churn"]),
                created_at=_spread_date((0, 90)),
            )
        )
        customer_count += 1
        if customer_count % 2000 == 0:
            session.flush()

    # Prediction history trail ------------------------------------------------
    existing = session.scalar(select(func.count()).select_from(Prediction)) or 0
    prediction_count = 0
    if existing == 0:
        for _, row in frame.iterrows():
            session.add(
                Prediction(
                    customer_id=str(row["customer_id"]),
                    probability=float(row["churn_probability"]),
                    risk_level=risk_level(float(row["churn_probability"])),
                    predicted_churn=bool(row["predicted_churn"]),
                    model_version=model_service.model_name(),
                    payload='{"source": "batch_seed"}',
                    created_at=_spread_date((0, 90)),
                )
            )
            prediction_count += 1
            if prediction_count % 2000 == 0:
                session.flush()

    # Demo user + audit trail --------------------------------------------------
    if session.scalar(select(func.count()).select_from(User)) == 0:
        session.add(
            User(
                email="analyst@churnplatform.dev",
                display_name="Platform Analyst",
                role="data_analyst",
            )
        )
        session.commit()

    session.add(
        AuditLog(
            actor="bootstrap",
            action="database.seeded",
            resource="customers",
            detail=f"seeded {customer_count} customers, {prediction_count} predictions",
        )
    )
    session.commit()
    return {"customers": customer_count, "predictions": prediction_count}


def audit(session: Session, action: str, resource: str, detail: str = "", actor: str = "anonymous", ip: str = "") -> None:
    """Write an audit log row; never raise on failure."""
    try:
        session.add(AuditLog(action=action, resource=resource, detail=detail[:500], actor=actor, ip=ip))
        session.commit()
    except Exception:
        session.rollback()
