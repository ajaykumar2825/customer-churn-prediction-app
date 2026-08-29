"""FastAPI application entrypoint.

Run with: ``uvicorn app.main:app --reload`` from the ``backend`` directory.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core import bootstrap
from app.core.cache import cache
from app.core.config import settings
from app.core.database import init_db
from app.core.exceptions import install_exception_handlers
from app.core.logging import setup_logging
from app.core.rate_limit import rate_limit_middleware
from app.services.model_service import model_service

bootstrap.ensure_repo_importable()
setup_logging()
logger = logging.getLogger("churn.main")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description=(
            "Enterprise telecom customer-churn analytics: model scoring, SHAP "
            "explainability, executive KPIs and business strategy. "
            "Interactive docs at /docs."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # --- CORS ------------------------------------------------------------------
    origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- rate limiting -----------------------------------------------------------
    app.middleware("http")(rate_limit_middleware)

    # --- exception -> JSON mapping ------------------------------------------------
    install_exception_handlers(app)

    # --- routes -------------------------------------------------------------------
    @app.get("/", include_in_schema=False)
    def root() -> dict:
        return {
            "service": settings.app_name,
            "docs": "/docs",
            "health": f"{settings.api_prefix}/health",
        }

    app.include_router(api_router)

    # unversioned convenience aliases for the spec'd endpoint list
    app.include_router(api_router, prefix="", include_in_schema=False)

    # --- startup -------------------------------------------------------------------
    @app.on_event("startup")
    def startup() -> None:
        logger.info("starting service", extra={"context": {"environment": settings.environment, "cache": cache.backend}})
        try:
            model_service.load()
            logger.info("model artefacts loaded", extra={"context": {"model": model_service.model_name()}})
        except Exception as exc:  # pragma: no cover - environment dependent
            logger.error("model load failed", extra={"context": {"error": str(exc)}})

        if settings.database_url:
            try:
                init_db()
                logger.info("database initialised")
                from app.services.seed_service import seed_database

                seed_database(clear=True)
                logger.info("database seeded")
            except Exception as exc:  # pragma: no cover - environment dependent
                logger.error("database initialisation failed", extra={"context": {"error": str(exc)}})

    return app


app = create_app()
