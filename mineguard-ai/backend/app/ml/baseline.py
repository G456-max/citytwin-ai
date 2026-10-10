"""
MineGuard AI - Baseline Risk Classification Model (Phase C3)
Implements balanced Logistic Regression with StandardScaler normalization.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report
)

from app.ml.features import FEATURE_NAMES


class BaselineRiskModel:
    """
    Interpretable baseline risk classifier using regularized Logistic Regression.
    """

    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.model = LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=self.random_state
        )
        self.feature_names: List[str] = list(FEATURE_NAMES)
        self.is_fitted: bool = False

    def fit(self, X_train: np.ndarray, y_train: np.ndarray, feature_names: Optional[List[str]] = None) -> "BaselineRiskModel":
        """
        Fits StandardScaler and LogisticRegression on training data.
        """
        if feature_names:
            self.feature_names = list(feature_names)

        X_scaled = self.scaler.fit_transform(X_train)
        self.model.fit(X_scaled, y_train)
        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predicts binary risk class (0 or 1)."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predict.")
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predicts class probabilities."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predict_proba.")
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)

    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, Any]:
        """
        Computes precision, recall, F1, ROC-AUC, and confusion matrix.
        """
        y_pred = self.predict(X_test)
        y_proba = self.predict_proba(X_test)[:, 1] if len(np.unique(y_test)) > 1 else y_pred.astype(float)

        acc = float(accuracy_score(y_test, y_pred))
        prec = float(precision_score(y_test, y_pred, zero_division=0))
        rec = float(recall_score(y_test, y_pred, zero_division=0))
        f1 = float(f1_score(y_test, y_pred, zero_division=0))

        try:
            auc = float(roc_auc_score(y_test, y_proba)) if len(np.unique(y_test)) > 1 else 1.0
        except Exception:
            auc = 1.0

        cm = confusion_matrix(y_test, y_pred).tolist()
        report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

        return {
            "accuracy": acc,
            "precision": prec,
            "recall": rec,
            "f1": f1,
            "roc_auc": auc,
            "confusion_matrix": cm,
            "classification_report": report
        }

    def save(self, path: str | Path) -> None:
        """Persists model artifact to disk."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, str(p))

    @classmethod
    def load(cls, path: str | Path) -> "BaselineRiskModel":
        """Loads model artifact from disk."""
        return joblib.load(str(path))

    def get_model_info(self) -> Dict[str, Any]:
        """Returns coefficient weights and model hyperparameters."""
        if not self.is_fitted:
            return {"model_type": "LogisticRegression", "is_fitted": False}

        coefs = self.model.coef_[0].tolist()
        coef_dict = {
            self.feature_names[i] if i < len(self.feature_names) else f"feat_{i}": round(float(coefs[i]), 4)
            for i in range(len(coefs))
        }

        return {
            "model_type": "LogisticRegression",
            "is_fitted": True,
            "intercept": round(float(self.model.intercept_[0]), 4),
            "coefficients": coef_dict,
            "hyperparameters": {
                "max_iter": self.model.max_iter,
                "class_weight": self.model.class_weight,
                "random_state": self.random_state
            }
        }
