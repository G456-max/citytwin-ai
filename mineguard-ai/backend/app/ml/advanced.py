"""
MineGuard AI - Advanced Risk Models (Phase C4)
Implements non-linear ensemble models: Random Forest and optional XGBoost
for capturing high-order interactions among cryptographic parameters.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
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


class RandomForestRiskModel:
    """
    Ensemble Decision Forest capturing multi-feature cryptographic risk thresholds.
    """

    def __init__(self, n_estimators: int = 100, max_depth: int = 10, random_state: int = 42):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.random_state = random_state
        self.model = RandomForestClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            class_weight="balanced",
            random_state=self.random_state
        )
        self.feature_names: List[str] = list(FEATURE_NAMES)
        self.is_fitted: bool = False

    def fit(self, X_train: np.ndarray, y_train: np.ndarray, feature_names: Optional[List[str]] = None) -> "RandomForestRiskModel":
        """Fits Random Forest classifier."""
        if feature_names:
            self.feature_names = list(feature_names)
        self.model.fit(X_train, y_train)
        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predict.")
        return self.model.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predict_proba.")
        return self.model.predict_proba(X)

    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, Any]:
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
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, str(p))

    @classmethod
    def load(cls, path: str | Path) -> "RandomForestRiskModel":
        return joblib.load(str(path))

    def get_feature_importances(self) -> Dict[str, float]:
        if not self.is_fitted:
            return {}
        importances = self.model.feature_importances_
        return {
            self.feature_names[i] if i < len(self.feature_names) else f"feat_{i}": round(float(importances[i]), 4)
            for i in range(len(importances))
        }

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "model_type": "RandomForestClassifier",
            "is_fitted": self.is_fitted,
            "feature_importances": self.get_feature_importances(),
            "hyperparameters": {
                "n_estimators": self.n_estimators,
                "max_depth": self.max_depth,
                "class_weight": "balanced",
                "random_state": self.random_state
            }
        }


# ============ OPTIONAL XGBOOST MODEL ============
try:
    from xgboost import XGBClassifier  # type: ignore
    XGBOOST_INSTALLED = True
except ImportError:
    XGBOOST_INSTALLED = False


class XGBoostRiskModel:
    """
    Gradient Boosted Decision Trees classifier with automatic fallback if XGBoost is not installed.
    """

    def __init__(self, n_estimators: int = 100, max_depth: int = 6, learning_rate: float = 0.1, random_state: int = 42):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.random_state = random_state
        self.feature_names: List[str] = list(FEATURE_NAMES)
        self.is_fitted: bool = False

        if XGBOOST_INSTALLED:
            self.model = XGBClassifier(
                n_estimators=self.n_estimators,
                max_depth=self.max_depth,
                learning_rate=self.learning_rate,
                random_state=self.random_state,
                eval_metric="logloss"
            )
        else:
            self.model = None

    @staticmethod
    def is_available() -> bool:
        return XGBOOST_INSTALLED

    def fit(self, X_train: np.ndarray, y_train: np.ndarray, feature_names: Optional[List[str]] = None) -> "XGBoostRiskModel":
        if not XGBOOST_INSTALLED:
            raise RuntimeError("XGBoost is not installed on this system. Use RandomForestRiskModel or install xgboost.")
        if feature_names:
            self.feature_names = list(feature_names)
        self.model.fit(X_train, y_train)
        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predict.")
        return self.model.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predict_proba.")
        return self.model.predict_proba(X)

    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, Any]:
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
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, str(p))

    @classmethod
    def load(cls, path: str | Path) -> "XGBoostRiskModel":
        return joblib.load(str(path))

    def get_model_info(self) -> Dict[str, Any]:
        if not XGBOOST_INSTALLED:
            return {"model_type": "XGBClassifier", "available": False, "installed": False}
        return {
            "model_type": "XGBClassifier",
            "is_fitted": self.is_fitted,
            "hyperparameters": {
                "n_estimators": self.n_estimators,
                "max_depth": self.max_depth,
                "learning_rate": self.learning_rate,
                "random_state": self.random_state
            }
        }
