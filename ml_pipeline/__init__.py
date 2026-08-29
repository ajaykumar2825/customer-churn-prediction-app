"""Customer Churn Prediction — ML pipeline.

Package layout
--------------
``config``      paths, constants, feature catalogue
``features``    raw -> engineered modelling frame
``preprocess``  sklearn preprocessor (the API contract)
``models``      classifier registry + factories
``tune``        Optuna hyper-parameter optimisation
``evaluate``    metrics, CV, thresholding, curves
``explain``     SHAP summaries and local explanations
``business``    revenue-at-risk, CLV, retention ROI, segments
``artifacts``   versioned persistence of trained objects
``pipeline``    ``python -m ml_pipeline.pipeline`` orchestrator
"""

from ml_pipeline.config import FEATURE_COLUMNS, NUMERIC_FEATURES, CATEGORIC_FEATURES  # noqa: F401

__version__ = "1.0.0"