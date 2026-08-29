"""Seed the platform database with the live model's predictions.

Run from the repository root:

    python -m database.seed                # uses DATABASE_URL / SQLite default
    DATABASE_URL=postgresql://... python -m database.seed --clear

This writes ~7,043 real customers (features + champion-model output), a
prediction-history trail spread over the last 90 days, a demo platform user
and sample audit events.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "backend"))

os.environ.setdefault("DATABASE_URL", "")


def main() -> None:
    import json

    from app.core import bootstrap
    from app.core.database import engine, init_db
    from app.services.model_service import model_service
    from app.services.seed_service import seed_database

    bootstrap.ensure_repo_importable()
    model_service.load()
    if not model_service.ready:
        raise SystemExit("Model artefacts not found. Run the ML pipeline first: python -m ml_pipeline.pipeline --tune-trials")
    init_db()
    summary = seed_database(clear="--clear" in sys.argv)
    print("Seeded:", json.dumps(summary))
    print("Database:", engine.url.render_as_string(hide_password=True))


if __name__ == "__main__":
    main()