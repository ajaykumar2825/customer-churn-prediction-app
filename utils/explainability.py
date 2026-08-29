"""Explainability: local SHAP for any row + global artefacts for the lab.

SHAP is imported lazily so pages that never show explanations stay light.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from ml_pipeline.explain import explain_local, natural_language_explanation


def pretty_feature(name: str) -> str:
    return name.replace("_", " · ").replace("MtM", "Month-to-month").title() if name else name


def local_explanation(model, preprocessor, row: pd.Series, churn_probability: float, threshold: float) -> dict[str, Any]:
    """Vector of SHAP contributions + plain-English factors for one customer."""
    row_frame = row.to_frame().T
    transformed = preprocessor.transform(row_frame)
    if hasattr(transformed, "toarray"):
        transformed = transformed.toarray()

    encoded_names = list(preprocessor.get_feature_names_out())
    result = explain_local(model, preprocessor, np.asarray(transformed), encoded_names)
    result["prediction"] = round(float(churn_probability), 4)
    result["threshold"] = float(threshold)

    factors = factors_to_values(result["contributions"], row)
    result["factors"] = factors
    result["narrative"] = natural_language_explanation(
        result["contributions"], factors, threshold, churn_probability
    )
    return result


def factors_to_values(contributions: list[dict[str, Any]], row: pd.Series) -> dict[str, Any]:
    """Mirror raw feature values next to the encoded SHAP names."""
    values: dict[str, Any] = {}
    for item in contributions:
        feature = item["feature"]
        base = feature.split("_")[0]
        if base in row.index:
            raw = row[base]
            try:
                values[feature] = float(raw)
            except (TypeError, ValueError):
                values[feature] = str(raw)
        else:
            values[feature] = 0.0
    return values