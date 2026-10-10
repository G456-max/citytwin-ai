"""
MineGuard AI - Model Training Engine (Phase C3/C4)
Trains baseline, random forest, and gradient boosted models, computes metrics,
saves artifacts, and logs metadata.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import networkx as nx

from app.ml.dataset import DatasetBuilder
from app.ml.baseline import BaselineRiskModel
from app.ml.advanced import RandomForestRiskModel, XGBoostRiskModel
from app.ml.model_registry import registry


class ModelTrainer:
    """
    End-to-end training pipeline for quantum risk models.
    """

    def __init__(self, model_type: str = "baseline", models_dir: str = "data/models"):
        self.model_type = model_type.lower().replace("-", "_")
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)

    def train(self, findings: List[Dict[str, Any]], graph: Optional[nx.DiGraph] = None) -> Tuple[Any, Dict[str, Any]]:
        """
        Executes end-to-end dataset building, model training, evaluation, and artifact serialization.
        """
        builder = DatasetBuilder()
        data = builder.build(findings, graph=graph)

        X_train, y_train = data["X_train"], data["y_train"]
        X_test, y_test = data["X_test"], data["y_test"]
        feature_names = data["feature_names"]

        if len(X_train) == 0:
            raise ValueError("Training dataset cannot be empty.")

        # Initialize model
        if self.model_type in {"baseline", "logistic_regression"}:
            model = BaselineRiskModel()
            type_label = "LogisticRegression"
        elif self.model_type in {"random_forest", "rf"}:
            model = RandomForestRiskModel()
            type_label = "RandomForest"
        elif self.model_type in {"xgboost", "xgb"}:
            model = XGBoostRiskModel()
            type_label = "XGBoost"
        else:
            raise ValueError(f"Unknown model_type: '{self.model_type}'. Choose from 'baseline', 'random_forest', 'xgboost'.")

        # Fit model
        model.fit(X_train, y_train, feature_names=feature_names)

        # Evaluate
        train_metrics = model.evaluate(X_train, y_train)
        test_metrics = model.evaluate(X_test, y_test)

        now_str = datetime.now(timezone.utc).isoformat()
        metadata = {
            "model_type": type_label,
            "trained_at": now_str,
            "n_samples": data["metadata"]["n_samples"],
            "feature_names": feature_names,
            "metrics": {
                "train": train_metrics,
                "test": test_metrics
            },
            "class_balance": data["metadata"]["class_balance"],
            "label_method": "rule_based_severity",
            "version": "1.0.0",
            "split_sizes": data["metadata"]["split_sizes"]
        }

        # Save artifacts
        model_filename = f"{self.model_type}.joblib"
        model_path = self.models_dir / model_filename
        model.save(model_path)

        # Register in registry
        registry.register(name=self.model_type, model=model, metadata=metadata)

        return model, metadata
