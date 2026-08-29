"""Bootstrap helper: puts the repository root on ``sys.path``.

This lets the FastAPI service reuse the exact feature-engineering code from
``ml_pipeline.features`` so the served predictions never drift from training.
"""

from __future__ import annotations

import os
import sys

from app.core.config import REPO_ROOT

_DONE = False


def ensure_repo_importable() -> None:
    global _DONE
    if _DONE:
        return
    root = str(REPO_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    os.environ.setdefault("REPO_ROOT", root)
    _DONE = True
