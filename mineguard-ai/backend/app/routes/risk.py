"""
MineGuard AI - Risk Scoring & ML Prediction Route (Phases C1 & C7)
Calculates aggregated risk scores, extracts 25-feature representations,
and delivers ML model predictions with explainability attributions.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from app.models.schemas import RiskRequest, RiskResponse, Finding
from app.ml.features import FeatureExtractor, FEATURE_NAMES
from app.ml.dataset import DatasetBuilder, DataLabeler
from app.ml.predictor import RiskPredictor

router = APIRouter(prefix="/risk", tags=["Risk & ML Inference"])

# Singleton predictor instance
predictor = RiskPredictor()


@router.post("", response_model=RiskResponse)
async def calculate_risk(request: RiskRequest):
    """
    Computes aggregated quantum risk score, severity, and Mosca exposure metrics across findings.
    """
    findings_dicts = [f.model_dump() if hasattr(f, "model_dump") else dict(f) for f in request.findings]

    if not findings_dicts:
        return RiskResponse(
            score=0,
            severity="SAFE",
            mosca_exposed=False,
            mosca_gap=0,
            breakdown={"total": 0, "critical": 0, "high": 0, "safe": 0}
        )

    # Use ML predictor for each finding
    preds = predictor.predict_batch(findings_dicts)
    scores = [p["score"] for p in preds]
    avg_score = int(sum(scores) / len(scores) * 100) if scores else 0

    crit_count = sum(1 for p in preds if p["severity"] == "CRITICAL")
    high_count = sum(1 for p in preds if p["severity"] == "HIGH")
    safe_count = sum(1 for p in preds if p["severity"] == "SAFE")

    overall_sev = "CRITICAL" if crit_count > 0 else ("HIGH" if high_count > 0 else "SAFE")
    mosca_exposed = crit_count > 0 or high_count > 0
    mosca_gap = 15 if mosca_exposed else 0

    return RiskResponse(
        score=max(avg_score, 95 if crit_count > 0 else 0),
        severity=overall_sev,
        mosca_exposed=mosca_exposed,
        mosca_gap=mosca_gap,
        breakdown={
            "total": len(findings_dicts),
            "critical": crit_count,
            "high": high_count,
            "safe": safe_count,
            "inference_mode": preds[0]["inference_mode"] if preds else "heuristic"
        }
    )


@router.post("/features")
async def extract_risk_features(payload: Dict[str, List[Dict[str, Any]]]):
    """
    Extracts 25-dimensional feature vectors for a list of findings,
    returning feature vectors alongside the responsible label definition.
    """
    raw_findings = payload.get("findings", [])
    extractor = FeatureExtractor()
    X, y, feature_names = extractor.transform(raw_findings)

    return {
        "feature_names": feature_names,
        "n_samples": len(X),
        "n_features": len(feature_names),
        "features": X.tolist(),
        "labels": y.tolist(),
        "label_definition": DataLabeler.get_label_definition()
    }


@router.post("/dataset")
async def build_risk_dataset(payload: Dict[str, List[Dict[str, Any]]]):
    """
    Builds stratified train/val/test splits and metadata from input findings.
    """
    raw_findings = payload.get("findings", [])
    builder = DatasetBuilder()
    data = builder.build(raw_findings)

    return {
        "metadata": data["metadata"],
        "train_samples": len(data["X_train"]),
        "val_samples": len(data["X_val"]),
        "test_samples": len(data["X_test"]),
        "feature_names": data["feature_names"]
    }


@router.post("/predict")
async def predict_risk(payload: Dict[str, Any]):
    """
    Predicts quantum risk probability, classification, confidence,
    and top attribution factors for one or more findings.
    """
    findings = payload.get("findings")
    if findings is None:
        # Check if single finding was passed directly
        if "algorithm" in payload or "file" in payload:
            findings = [payload]
        else:
            findings = []

    predictions = predictor.predict_batch(findings)
    model_info = predictor.model.get_model_info() if predictor.model else {"model_type": "RuleBasedFallback"}

    return {
        "predictions": predictions,
        "count": len(predictions),
        "model_type": model_info.get("model_type", "RuleBasedFallback"),
        "model_version": "1.0.0"
    }


@router.post("/predict-batch")
async def predict_risk_batch(payload: Dict[str, List[Dict[str, Any]]]):
    """
    Batch prediction endpoint for large findings callsets.
    """
    raw_findings = payload.get("findings", [])
    predictions = predictor.predict_batch(raw_findings)

    return {
        "predictions": predictions,
        "total": len(predictions)
    }


@router.get("/model-info")
async def get_active_model_info():
    """
    Returns architecture, coefficients, and hyperparameters of the currently active model.
    """
    if predictor.model and hasattr(predictor.model, "get_model_info"):
        return predictor.model.get_model_info()
    return {
        "model_type": "RuleBasedFallback",
        "is_fitted": False,
        "status": "No trained model active; heuristic fallback active"
    }
