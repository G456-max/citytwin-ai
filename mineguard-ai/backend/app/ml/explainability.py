"""
MineGuard AI - Model Explainability & Feature Attribution Engine (Phase C6)
Computes per-prediction feature contributions, waterfall plots, and global importance rankings.
Includes native mathematical fallback when SHAP library is not installed.
"""

import io
import base64
from typing import Dict, Any, List, Optional
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from app.ml.features import FEATURE_NAMES

try:
    import shap  # type: ignore
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False


class SHAPExplainer:
    """
    Explains risk model predictions using SHAP values or linear/tree attribution coefficients.
    """

    def __init__(self, model: Any, feature_names: Optional[List[str]] = None):
        self.model = model
        self.feature_names = list(feature_names or FEATURE_NAMES)
        self.shap_explainer = None

        if SHAP_AVAILABLE:
            try:
                underlying = getattr(self.model, "model", self.model)
                self.shap_explainer = shap.Explainer(underlying)
            except Exception:
                self.shap_explainer = None

    def explain_instance(self, features: List[float] | np.ndarray) -> Dict[str, Any]:
        """
        Calculates local feature attributions for a single instance.
        """
        x_arr = np.array(features, dtype=np.float64).reshape(1, -1)

        # 1. Attempt SHAP explainer
        if self.shap_explainer is not None:
            try:
                shap_res = self.shap_explainer(x_arr)
                vals = shap_res.values[0]
                if len(vals.shape) > 1:
                    vals = vals[:, 1]  # positive class
                return {
                    "method": "SHAP",
                    "contributions": {
                        self.feature_names[i]: round(float(vals[i]), 4)
                        for i in range(min(len(self.feature_names), len(vals)))
                    }
                }
            except Exception:
                pass

        # 2. Native mathematical attribution fallback
        contributions: Dict[str, float] = {}
        underlying = getattr(self.model, "model", self.model)

        if hasattr(underlying, "coef_"):
            # Logistic Regression attribution: feature_value * weight
            coefs = underlying.coef_[0]
            # If model has scaler
            if hasattr(self.model, "scaler") and self.model.scaler is not None:
                x_scaled = self.model.scaler.transform(x_arr)[0]
            else:
                x_scaled = x_arr[0]

            for i in range(min(len(self.feature_names), len(coefs))):
                val = float(x_scaled[i] * coefs[i])
                contributions[self.feature_names[i]] = round(val, 4)

        elif hasattr(underlying, "feature_importances_"):
            # Tree attribution: feature_importance * (x_val - 0.5)
            importances = underlying.feature_importances_
            raw_x = x_arr[0]
            for i in range(min(len(self.feature_names), len(importances))):
                val = float(importances[i] * (raw_x[i] - 0.2))
                contributions[self.feature_names[i]] = round(val, 4)

        else:
            # Equal heuristic attribution based on feature values
            raw_x = x_arr[0]
            for i in range(min(len(self.feature_names), len(raw_x))):
                contributions[self.feature_names[i]] = round(float(raw_x[i]), 4)

        return {
            "method": "FeatureAttributionFallback",
            "contributions": contributions
        }

    def explain_batch(self, X: np.ndarray) -> List[Dict[str, Any]]:
        """Explains an entire batch of feature vectors."""
        return [self.explain_instance(row) for row in X]

    def get_top_features(self, contributions: Dict[str, float], n: int = 5) -> List[Dict[str, Any]]:
        """Returns top n features ranked by magnitude of risk contribution."""
        sorted_feats = sorted(
            contributions.items(),
            key=lambda item: abs(item[1]),
            reverse=True
        )
        return [
            {
                "feature": k,
                "importance": v,
                "direction": "increases_risk" if v > 0 else "reduces_risk"
            }
            for k, v in sorted_feats[:n]
        ]

    def plot_waterfall(self, contributions: Dict[str, float]) -> str:
        """Renders horizontal waterfall bar chart of top 8 factors and returns base64 PNG."""
        top_items = sorted(contributions.items(), key=lambda x: abs(x[1]), reverse=True)[:8]
        top_items.reverse()

        feats = [item[0] for item in top_items]
        vals = [item[1] for item in top_items]
        colors = ["#ef4444" if v >= 0 else "#10b981" for v in vals]

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.barh(feats, vals, color=colors)
        ax.axvline(0, color="#64748b", linestyle="--", linewidth=0.8)
        ax.set_title("Top Risk Attribution Factors", fontweight="bold", pad=12)
        ax.set_xlabel("Attribution Value", fontweight="bold")
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=100)
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode("utf-8")
