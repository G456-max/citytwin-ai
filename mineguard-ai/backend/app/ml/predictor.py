"""
MineGuard AI - Risk Inference Engine (Phase C7)
Loads trained ML risk models, extracts real-time 25-feature representations,
generates probabilistic risk scores, and provides robust rule-based fallbacks.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np

from app.ml.features import FeatureExtractor
from app.ml.model_registry import registry
from app.ml.explainability import SHAPExplainer


class RiskPredictor:
    """
    Production inference engine with automatic model loading and graceful rule-based fallback.
    """

    def __init__(self, model_path: Optional[str | Path] = None):
        self.model_path = Path(model_path) if model_path else None
        self.model = None
        self.explainer = None
        self.extractor = FeatureExtractor()
        self._load_model()

    def _load_model(self) -> None:
        """Attempts to load model from path, registry, or standard disk location."""
        # 1. Direct path
        if self.model_path and self.model_path.exists():
            import joblib
            try:
                self.model = joblib.load(str(self.model_path))
            except Exception:
                self.model = None

        # 2. Registry or default models directory
        if not self.model:
            # Check best model in registry
            best_name = registry.select_best(metric="f1") or "baseline"
            self.model = registry.get(best_name)

        # 3. Fallback to data/models/baseline.joblib
        if not self.model:
            candidate = Path("data/models/baseline.joblib")
            if candidate.exists():
                import joblib
                try:
                    self.model = joblib.load(str(candidate))
                except Exception:
                    self.model = None

        if self.model:
            self.explainer = SHAPExplainer(self.model)

    def predict(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predicts quantum risk score, severity category, confidence level, and top attribution factors.
        """
        # Rule-based fallback if no model is loaded
        if not self.model:
            return self._rule_based_fallback(finding)

        try:
            feats = self.extractor.extract_features(finding)
            X = np.array(feats, dtype=np.float64).reshape(1, -1)

            if hasattr(self.model, "predict_proba"):
                probas = self.model.predict_proba(X)[0]
                risk_score = float(probas[1]) if len(probas) > 1 else float(self.model.predict(X)[0])
            else:
                pred = int(self.model.predict(X)[0])
                risk_score = 1.0 if pred == 1 else 0.0

            # Compute explanation
            top_factors = []
            if self.explainer:
                exp = self.explainer.explain_instance(feats)
                top_factors = self.explainer.get_top_features(exp.get("contributions", {}), n=3)

            # Classify severity
            if risk_score >= 0.7:
                sev = "CRITICAL"
            elif risk_score >= 0.4:
                sev = "MEDIUM"
            else:
                sev = "SAFE"

            model_name = getattr(self.model, "model_type", type(self.model).__name__)

            return {
                "score": round(risk_score, 4),
                "severity": sev,
                "confidence": "high" if (risk_score >= 0.85 or risk_score <= 0.15) else "medium",
                "top_factors": top_factors,
                "model_type": model_name,
                "inference_mode": "ml_model"
            }
        except Exception:
            # Fall back gracefully on error
            return self._rule_based_fallback(finding)

    def predict_batch(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Processes a list of findings in batch."""
        return [self.predict(f) for f in findings]

    def _rule_based_fallback(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deterministic rule-based fallback when ML model artifact is unavailable.
        """
        raw_sev = str(finding.get("severity", "MEDIUM")).upper()
        algo = str(finding.get("algorithm", "")).upper()

        if raw_sev in {"CRITICAL", "HIGH"} or any(k in algo for k in ["RSA", "ECDSA", "DH"]):
            score = 1.0
            sev = "CRITICAL"
        elif raw_sev == "MEDIUM" or "AES-128" in algo:
            score = 0.5
            sev = "MEDIUM"
        else:
            score = 0.0
            sev = "SAFE"

        return {
            "score": score,
            "severity": sev,
            "confidence": "medium",
            "top_factors": [
                {"feature": "algorithm_vulnerability", "importance": 1.0, "direction": "increases_risk"}
            ],
            "model_type": "RuleBasedFallback",
            "inference_mode": "heuristic"
        }
