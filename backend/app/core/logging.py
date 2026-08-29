"""Structured JSON logging for the API service.

Emits one JSON object per line so the output can be shipped to any log
aggregator (CloudWatch, Logz.io, Loki…) without custom adapters.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    """Render log records as single-line JSON documents."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        extra = getattr(record, "context", None)
        if extra:
            payload["context"] = extra
        return json.dumps(payload, default=str)


def setup_logging(level: int = logging.INFO) -> None:
    """Idempotent root configuration."""
    root = logging.getLogger()
    if any(isinstance(h.formatter, JsonFormatter) for h in root.handlers):
        return
    root.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    # Keep uvicorn access logs readable instead of JSON-silent
    logging.getLogger("uvicorn.error").propagate = False


def get_logger(name: str) -> logging.Logger:
    """Logger factory that attaches structured context helpers."""
    logger = logging.getLogger(name)

    def with_context(**context):
        class _Ctx:
            def debug(self, msg): logger.debug(msg, extra={"context": context})
            def info(self, msg): logger.info(msg, extra={"context": context})
            def warning(self, msg): logger.warning(msg, extra={"context": context})
            def error(self, msg): logger.error(msg, extra={"context": context})

        return _Ctx()

    logger.with_context = with_context  # type: ignore[attr-defined]
    return logger
