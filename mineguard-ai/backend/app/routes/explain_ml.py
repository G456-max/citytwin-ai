"""
MineGuard AI - Explainable ML Route (Phase C6)
Delivers per-prediction feature attributions, waterfall charts, and global feature importance.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException

from app.ml.predictor import RiskPredictor
from app.ml.explainability import SHAPExplainer
from app.ml.model_registry import registry
from app.ml.features import FEATURE_NAMES

router = APIRouter(prefix="/explain-ml", tags=["Explainable AI"])
predictor = RiskPredictor()


@router.post("/predict-with-reasons")
async def predict_with_reasons(payload: Dict[str, Any]):
    """
    Computes risk prediction and returns the top 5 contributing feature factors.
    """
    finding = payload.get("finding") or payload
    pred = predictor.predict(finding)

    waterfall_plot = None
    if predictor.explainer:
        feats = predictor.extractor.extract_features(finding)
        exp = predictor.explainer.explain_instance(feats)
        waterfall_plot = predictor.explainer.plot_waterfall(exp.get("contributions", {}))

    return {
        "prediction": pred,
        "top_factors": pred.get("top_factors", []),
        "waterfall_plot": waterfall_plot
    }


@router.post("/feature-importance")
async def get_feature_importance(payload: Optional[Dict[str, Any]] = None):
    """
    Returns global feature importance ranking for the active or requested model.
    """
    model_name = payload.get("model_name", "random_forest") if payload else "random_forest"
    model = registry.get(model_name) or predictor.model

    if not model:
        return {
            "model_name": "None",
            "feature_importance": {f: 1.0 / len(FEATURE_NAMES) for f in FEATURE_NAMES}
        }

    underlying = getattr(model, "model", model)
    importance_dict = {}

    if hasattr(underlying, "feature_importances_"):
        imps = underlying.feature_importances_
        importance_dict = {
            FEATURE_NAMES[i]: round(float(imps[i]), 4)
            for i in range(min(len(FEATURE_NAMES), len(imps)))
        }
    elif hasattr(underlying, "coef_"):
        coefs = abs(underlying.coef_[0])
        total = sum(coefs) or 1.0
        importance_dict = {
            FEATURE_NAMES[i]: round(float(coefs[i] / total), 4)
            for i in range(min(len(FEATURE_NAMES), len(coefs)))
        }

    sorted_imps = sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)

    return {
        "model_name": model_name,
        "ranked_features": [{"feature": k, "importance": v} for k, v in sorted_imps]
    }


@router.post("/shap-summary")
async def get_shap_summary(payload: Optional[Dict[str, Any]] = None):
    """
    Generates summary attribution distribution across test samples.
    """
    findings = payload.get("findings", []) if payload else []
    if not findings:
        from app.ml.dataset_builder import SyntheticDatasetGenerator
        findings = SyntheticDatasetGenerator().generate(n_samples=50)

    explainer = predictor.explainer or SHAPExplainer(predictor.model)
    X = [predictor.extractor.extract_features(f) for f in findings]
    explanations = [explainer.explain_instance(row) for row in X]

    # Aggregate average absolute contribution per feature
    agg: Dict[str, float] = {f: 0.0 for f in FEATURE_NAMES}
    for e in explanations:
        for k, v in e.get("contributions", {}).items():
            if k in agg:
                agg[k] += abs(v)

    n = len(explanations) or 1
    mean_imp = {k: round(v / n, 4) for k, v in agg.items()}
    sorted_mean = sorted(mean_imp.items(), key=lambda x: x[1], reverse=True)

    waterfall_plot = explainer.plot_waterfall(mean_imp)

    return {
        "n_samples_analyzed": len(findings),
        "mean_importance": [{"feature": k, "mean_contribution": v} for k, v in sorted_mean],
        "summary_plot": waterfall_plot
    }
