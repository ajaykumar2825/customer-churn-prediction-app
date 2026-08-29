"""SQLAlchemy engine, session factory and declarative base.

Supports PostgreSQL (production) and SQLite (local development) transparently;
the driver/URL is resolved from ``DATABASE_URL``.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """Declarative base for every ORM table."""


def _resolve_url() -> str:
    if settings.database_url:
        return settings.database_url
    # SQLite development default persisted inside the backend package.
    from app.core.config import REPO_ROOT

    return f"sqlite:///{(REPO_ROOT / 'backend' / 'app' / 'data' / 'churn.db').as_posix()}"


def _create_engine():
    url = _resolve_url()
    kwargs: dict = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **kwargs)


engine = _create_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def init_db() -> None:
    """Create all tables if they do not exist."""
    from app.models import orm  # noqa: F401  (import registers mappings)

    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def database_online() -> bool:
    """Cheap reachability probe used to fall back to the in-memory store."""
    from sqlalchemy import text

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
