"""
MineGuard AI - Model Training Routes (Phases C3 & C4)
Exposes endpoints to trigger model training, benchmark comparisons, and artifact serialization.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException
from loguru import logger

from app.ml.trainer import ModelTrainer
from app.ml.model_registry import registry
from app.ml.dataset_builder import SyntheticDatasetGenerator
from app.ml.advanced import XGBoostRiskModel

router = APIRouter(prefix="/train", tags=["Model Training"])


def _get_findings_or_synthetic(payload: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Helper to extract findings from payload or generate synthetic dataset."""
    if payload and "findings" in payload and payload["findings"]:
        return payload["findings"]
    generator = SyntheticDatasetGenerator()
    n = payload.get("n_samples", 500) if payload else 500
    return generator.generate(n_samples=n)


@router.post("/baseline")
async def train_baseline(payload: Optional[Dict[str, Any]] = None):
    """
    Trains regularized Logistic Regression baseline model.
    """
    findings = _get_findings_or_synthetic(payload)
    trainer = ModelTrainer(model_type="baseline")
    model, metadata = trainer.train(findings)

    return {
        "status": "success",
        "model_type": metadata["model_type"],
        "metrics": metadata["metrics"]["test"],
        "metadata": metadata
    }


@router.post("/random-forest")
async def train_random_forest(payload: Optional[Dict[str, Any]] = None):
    """
    Trains Random Forest ensemble risk classifier.
    """
    findings = _get_findings_or_synthetic(payload)
    trainer = ModelTrainer(model_type="random_forest")
    model, metadata = trainer.train(findings)

    return {
        "status": "success",
        "model_type": metadata["model_type"],
        "metrics": metadata["metrics"]["test"],
        "metadata": metadata
    }


@router.post("/xgboost")
async def train_xgboost(payload: Optional[Dict[str, Any]] = None):
    """
    Trains XGBoost gradient boosted classifier if xgboost library is installed.
    """
    if not XGBoostRiskModel.is_available():
        raise HTTPException(
            status_code=501,
            detail="XGBoost is not installed on this system. Please use /train/random-forest."
        )

    findings = _get_findings_or_synthetic(payload)
    trainer = ModelTrainer(model_type="xgboost")
    model, metadata = trainer.train(findings)

    return {
        "status": "success",
        "model_type": metadata["model_type"],
        "metrics": metadata["metrics"]["test"],
        "metadata": metadata
    }


@router.post("/compare")
async def train_and_compare(payload: Optional[Dict[str, Any]] = None):
    """
    Trains baseline and random forest (and xgboost if available),
    returning side-by-side performance comparison metrics.
    """
    findings = _get_findings_or_synthetic(payload)

    # Train Baseline
    t_base = ModelTrainer(model_type="baseline")
    t_base.train(findings)

    # Train Random Forest
    t_rf = ModelTrainer(model_type="random_forest")
    t_rf.train(findings)

    if XGBoostRiskModel.is_available():
        t_xgb = ModelTrainer(model_type="xgboost")
        t_xgb.train(findings)

    comparison = registry.compare_models()
    best_model = registry.select_best(metric="f1")

    return {
        "comparison": comparison,
        "best_model": best_model,
        "metric_used": "f1"
    }


@router.get("/models")
async def list_registered_models():
    """
    Lists all models registered in the model registry.
    """
    return {
        "models": registry.list_all(),
        "total": len(registry.list_all()),
        "best_model": registry.select_best(metric="f1")
    }


@router.post("/synthetic")
async def generate_and_train(payload: Optional[Dict[str, Any]] = None):
    """
    Synthesizes realistic mining OT findings and trains the specified model.
    """
    model_type = payload.get("model_type", "baseline") if payload else "baseline"
    n_samples = payload.get("n_samples", 500) if payload else 500

    generator = SyntheticDatasetGenerator()
    findings = generator.generate(n_samples=n_samples)

    trainer = ModelTrainer(model_type=model_type)
    model, metadata = trainer.train(findings)

    return {
        "status": "success",
        "dataset": "SYNTHETIC",
        "n_samples": n_samples,
        "model_type": metadata["model_type"],
        "test_metrics": metadata["metrics"]["test"]
    }
