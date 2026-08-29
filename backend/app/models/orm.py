"""SQLAlchemy ORM models for the churn platform."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Customer(Base):
    """A telecom customer with the latest predicted churn state."""

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    senior_citizen: Mapped[bool] = mapped_column(Boolean, default=False)
    gender_female: Mapped[bool] = mapped_column(Boolean, default=False)
    partner: Mapped[bool] = mapped_column(Boolean, default=False)
    dependents: Mapped[bool] = mapped_column(Boolean, default=False)
    tenure: Mapped[int] = mapped_column(Integer, default=0)
    monthly_charges: Mapped[float] = mapped_column(Float, default=0.0)
    total_charges: Mapped[float] = mapped_column(Float, default=0.0)
    avg_monthly_charge: Mapped[float] = mapped_column(Float, default=0.0)
    paperless_billing: Mapped[bool] = mapped_column(Boolean, default=False)
    multi_line: Mapped[bool] = mapped_column(Boolean, default=False)
    online_security: Mapped[bool] = mapped_column(Boolean, default=False)
    online_backup: Mapped[bool] = mapped_column(Boolean, default=False)
    device_protection: Mapped[bool] = mapped_column(Boolean, default=False)
    tech_support: Mapped[bool] = mapped_column(Boolean, default=False)
    streaming_tv: Mapped[bool] = mapped_column(Boolean, default=False)
    streaming_movies: Mapped[bool] = mapped_column(Boolean, default=False)
    total_services: Mapped[int] = mapped_column(Integer, default=0)
    internet_service: Mapped[str] = mapped_column(String(16), default="No")
    contract: Mapped[str] = mapped_column(String(32), default="Month-to-month")
    payment_method: Mapped[str] = mapped_column(String(64), default="Electronic check")

    churn_probability: Mapped[float] = mapped_column(Float, default=0.0)
    risk_level: Mapped[str] = mapped_column(String(16), default="low")
    predicted_churn: Mapped[bool] = mapped_column(Boolean, default=False)
    observed_churn: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Prediction(Base):
    """One prediction event for one customer."""

    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    probability: Mapped[float] = mapped_column(Float, default=0.0)
    risk_level: Mapped[str] = mapped_column(String(16), default="low")
    predicted_churn: Mapped[bool] = mapped_column(Boolean, default=False)
    model_version: Mapped[str] = mapped_column(String(32), default="default")
    payload: Mapped[str] = mapped_column(Text, default="{}")
    explanation: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class User(Base):
    """Platform user (seeded for demo; no auth enforced in this release)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), default="")
    role: Mapped[str] = mapped_column(String(32), default="analyst")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class AuditLog(Base):
    """Append-only audit trail for sensitive actions."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor: Mapped[str] = mapped_column(String(120), default="anonymous")
    action: Mapped[str] = mapped_column(String(64), index=True)
    resource: Mapped[str] = mapped_column(String(120), default="")
    detail: Mapped[str] = mapped_column(Text, default="")
    ip: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
