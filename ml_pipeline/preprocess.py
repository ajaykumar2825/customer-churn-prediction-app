"""Sklearn preprocessing pipeline shared between training and inference.

The exact preprocessor object shipped to ``models/preprocessor.joblib`` is
created by :func:`build_preprocessor` so the backend must only ever call
``preprocessor.transform(...)``.
"""

from __future__ import annotations

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from ml_pipeline.config import CATEGORIC_FEATURES, NUMERIC_FEATURES


def build_preprocessor() -> Pipeline:
    """Return the canonical numeric/categorical preprocessor."""
    numeric_pipe = Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]
    )

    categoric_pipe = Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="most_frequent")),
            (
                "onehot",
                OneHotEncoder(handle_unknown="ignore", drop=None),
            ),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipe, NUMERIC_FEATURES),
            ("categoric", categoric_pipe, CATEGORIC_FEATURES),
        ],
        verbose_feature_names_out=False,
    )


def encoded_feature_names(preprocessor: ColumnTransformer, category_values: list[str] | None = None) -> list[str]:
    """Return the post-transform feature names produced by the preprocessor.

    ``category_values`` may be passed to guarantee stability even before the
    transformer was fitted; otherwise the transformer's fitted output names are
    used.
    """
    return list(preprocessor.get_feature_names_out())