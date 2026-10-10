"""
MineGuard AI - Model Evaluation Route (Phase C5)
Provides API endpoints for model evaluation, cross-validation, and performance reports.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException
import numpy as np

from app.ml.evaluator import ModelEvaluator
from app.ml.model_registry import registry
from app.ml.dataset import DatasetBuilder
from app.ml.dataset_builder import SyntheticDatasetGenerator

router = APIRouter(prefix="/evaluate", tags=["Model Evaluation"])
evaluator = ModelEvaluator()


@router.post("/model")
async def evaluate_saved_model(payload: Dict[str, Any]):
    """
    Evaluates a registered model on provided findings or synthetic test set.
    """
    model_name = payload.get("model_name", "baseline")
    model = registry.get(model_name)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found in registry.")

    findings = payload.get("findings")
    if not findings:
        findings = SyntheticDatasetGenerator().generate(n_samples=300)

    builder = DatasetBuilder()
    data = builder.build(findings)
    X_test, y_test = data["X_test"], data["y_test"]

    metrics = evaluator.evaluate_model(model, X_test, y_test)
    cm_base64 = evaluator.plot_confusion_matrix(metrics["confusion_matrix"])

    return {
        "model_name": model_name,
        "metrics": metrics,
        "confusion_matrix_plot": cm_base64
    }


@router.post("/cross-validate")
async def cross_validate_model(payload: Dict[str, Any]):
    """
    Executes k-fold cross validation for a model.
    """
    model_name = payload.get("model_name", "baseline")
    model = registry.get(model_name)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found.")

    findings = payload.get("findings")
    if not findings:
        findings = SyntheticDatasetGenerator().generate(n_samples=300)

    builder = DatasetBuilder()
    data = builder.build(findings)
    X, y = data["X_train"], data["y_train"]

    cv_results = evaluator.cross_validate(model, X, y, cv=payload.get("cv", 5))
    return {
        "model_name": model_name,
        "cv_results": cv_results
    }


@router.get("/report/{model_name}")
async def get_model_report(model_name: str):
    """
    Retrieves full evaluation report, hyperparameters, and plots for a registered model.
    """
    meta = registry.get_metadata(model_name)
    if not meta:
        raise HTTPException(status_code=404, detail=f"Metadata for model '{model_name}' not found.")

    test_metrics = meta.get("metrics", {}).get("test", {})
    cm = test_metrics.get("confusion_matrix")
    cm_plot = evaluator.plot_confusion_matrix(cm) if cm else None

    return {
        "model_name": model_name,
        "metadata": meta,
        "metrics": test_metrics,
        "confusion_matrix_plot": cm_plot
    }
