"""
Unit Tests for Machine Learning Models, Training, Evaluation, and Registry (Phases C3, C4, C5)
"""

import pytest
import numpy as np
from pathlib import Path

from app.ml.dataset_builder import SyntheticDatasetGenerator
from app.ml.dataset import DatasetBuilder
from app.ml.baseline import BaselineRiskModel
from app.ml.advanced import RandomForestRiskModel
from app.ml.trainer import ModelTrainer
from app.ml.model_registry import ModelRegistry
from app.ml.evaluator import ModelEvaluator


@pytest.fixture
def dataset_data():
    generator = SyntheticDatasetGenerator(seed=42)
    findings = generator.generate(n_samples=250)
    builder = DatasetBuilder(seed=42)
    return builder.build(findings)


# 1. test_baseline_trains
def test_baseline_trains(dataset_data):
    X_train, y_train = dataset_data["X_train"], dataset_data["y_train"]
    model = BaselineRiskModel()
    model.fit(X_train, y_train, feature_names=dataset_data["feature_names"])
    assert model.is_fitted is True


# 2. test_baseline_predicts
def test_baseline_predicts(dataset_data):
    X_train, y_train = dataset_data["X_train"], dataset_data["y_train"]
    X_test = dataset_data["X_test"]
    model = BaselineRiskModel()
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    probas = model.predict_proba(X_test)

    assert len(preds) == len(X_test)
    assert set(np.unique(preds)).issubset({0, 1})
    assert probas.shape == (len(X_test), 2)


# 3. test_baseline_metrics_present
def test_baseline_metrics_present(dataset_data):
    X_train, y_train = dataset_data["X_train"], dataset_data["y_train"]
    X_test, y_test = dataset_data["X_test"], dataset_data["y_test"]
    model = BaselineRiskModel()
    model.fit(X_train, y_train)

    metrics = model.evaluate(X_test, y_test)
    for key in ["accuracy", "precision", "recall", "f1", "roc_auc", "confusion_matrix"]:
        assert key in metrics
        assert metrics[key] is not None


# 4. test_random_forest_trains
def test_random_forest_trains(dataset_data):
    X_train, y_train = dataset_data["X_train"], dataset_data["y_train"]
    X_test, y_test = dataset_data["X_test"], dataset_data["y_test"]
    rf = RandomForestRiskModel(n_estimators=50, max_depth=5)
    rf.fit(X_train, y_train, feature_names=dataset_data["feature_names"])

    assert rf.is_fitted is True
    metrics = rf.evaluate(X_test, y_test)
    assert metrics["f1"] >= 0.8
    assert len(rf.get_feature_importances()) == 25


# 5. test_model_registry(tmp_path)
def test_model_registry(tmp_path: Path):
    reg = ModelRegistry(registry_dir=str(tmp_path / "models"))
    dummy_model = {"name": "test_model"}
    reg.register("model_a", dummy_model, {"metrics": {"test": {"f1": 0.88}}})
    reg.register("model_b", dummy_model, {"metrics": {"test": {"f1": 0.94}}})

    all_models = reg.list_all()
    assert len(all_models) == 2
    best = reg.select_best(metric="f1")
    assert best == "model_b"


# 6. test_evaluator_metrics(dataset_data)
def test_evaluator_metrics(dataset_data):
    X_train, y_train = dataset_data["X_train"], dataset_data["y_train"]
    X_test, y_test = dataset_data["X_test"], dataset_data["y_test"]

    model = BaselineRiskModel().fit(X_train, y_train)
    evaluator = ModelEvaluator()
    res = evaluator.evaluate_model(model, X_test, y_test)

    assert "f1" in res
    assert "confusion_matrix" in res
    cm_plot = evaluator.plot_confusion_matrix(res["confusion_matrix"])
    assert isinstance(cm_plot, str) and len(cm_plot) > 100


# 7. test_cross_validation(dataset_data)
def test_cross_validation(dataset_data):
    X_train, y_train = dataset_data["X_train"], dataset_data["y_train"]
    model = BaselineRiskModel().fit(X_train, y_train)
    evaluator = ModelEvaluator()
    cv_res = evaluator.cross_validate(model, X_train, y_train, cv=3)

    assert cv_res["cv_folds"] == 3
    assert len(cv_res["scores"]) == 3
    assert 0.0 <= cv_res["mean_f1"] <= 1.0


# 8. test_model_persistence(tmp_path, dataset_data)
def test_model_persistence(tmp_path: Path, dataset_data):
    X_train, y_train = dataset_data["X_train"], dataset_data["y_train"]
    X_test = dataset_data["X_test"]

    model = BaselineRiskModel().fit(X_train, y_train)
    save_path = tmp_path / "baseline_test.joblib"
    model.save(save_path)

    loaded = BaselineRiskModel.load(save_path)
    pred_orig = model.predict(X_test)
    pred_loaded = loaded.predict(X_test)

    np.testing.assert_array_equal(pred_orig, pred_loaded)
