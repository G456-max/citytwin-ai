"""
MineGuard AI - Machine Learning Package (Phases C1–C7)
Full ML pipeline for quantum vulnerability risk prediction, feature engineering,
model training, evaluation, explainability, and inference.
"""

from app.ml.features import (
    FeatureExtractor,
    FEATURE_NAMES,
    SEVERITY_SCORES,
    COMPLEXITY_SCORES,
    URGENCY_SCORES,
    CRITICALITY_SCORES,
    EXPOSURE_SCORES,
    SHOR_BROKEN,
    GROVER_WEAKENED,
)
from app.ml.dataset import DatasetBuilder, DataLabeler
from app.ml.dataset_builder import SyntheticDatasetGenerator
from app.ml.real_dataset import RealDatasetIngester
from app.ml.baseline import BaselineRiskModel
from app.ml.advanced import RandomForestRiskModel, XGBoostRiskModel
from app.ml.model_registry import ModelRegistry, registry
from app.ml.trainer import ModelTrainer
from app.ml.evaluator import ModelEvaluator
from app.ml.explainability import SHAPExplainer
from app.ml.predictor import RiskPredictor
from app.ml.model_card import ModelCard

__all__ = [
    # Feature Engineering (C1)
    "FeatureExtractor",
    "FEATURE_NAMES",
    "SEVERITY_SCORES",
    "COMPLEXITY_SCORES",
    "URGENCY_SCORES",
    "CRITICALITY_SCORES",
    "EXPOSURE_SCORES",
    "SHOR_BROKEN",
    "GROVER_WEAKENED",
    # Dataset Preparation (C2)
    "DatasetBuilder",
    "DataLabeler",
    "SyntheticDatasetGenerator",
    "RealDatasetIngester",
    # Models (C3 / C4)
    "BaselineRiskModel",
    "RandomForestRiskModel",
    "XGBoostRiskModel",
    # Training & Registry (C3 / C4)
    "ModelTrainer",
    "ModelRegistry",
    "registry",
    # Evaluation (C5)
    "ModelEvaluator",
    # Explainability (C6)
    "SHAPExplainer",
    # Deployment & Inference (C7)
    "RiskPredictor",
    "ModelCard",
]
