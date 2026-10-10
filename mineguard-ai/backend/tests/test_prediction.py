"""
Unit Tests for Risk Inference Engine and Prediction Endpoints (Phase C7)
"""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.ml.predictor import RiskPredictor
from app.ml.dataset_builder import SyntheticDatasetGenerator
from app.ml.trainer import ModelTrainer


client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_trained_model(tmp_path_factory):
    """Ensures at least one trained baseline model is saved for test suite."""
    gen = SyntheticDatasetGenerator(seed=42)
    findings = gen.generate(n_samples=100)
    trainer = ModelTrainer(model_type="baseline")
    trainer.train(findings)


# 1. test_predictor_loads
def test_predictor_loads():
    predictor = RiskPredictor()
    assert predictor is not None
    assert predictor.extractor is not None


# 2. test_predictor_fallback_when_no_model
def test_predictor_fallback_when_no_model(tmp_path: Path):
    non_existent = tmp_path / "ghost_model.joblib"
    predictor = RiskPredictor(model_path=non_existent)
    # Force model to None
    predictor.model = None

    finding = {"file": "auth.py", "algorithm": "RSA-2048", "severity": "CRITICAL"}
    res = predictor.predict(finding)

    assert res["score"] == 1.0
    assert res["severity"] == "CRITICAL"
    assert res["inference_mode"] == "heuristic"


# 3. test_predict_single_finding
def test_predict_single_finding():
    predictor = RiskPredictor()
    finding = {"file": "scada.py", "algorithm": "ECDSA", "severity": "CRITICAL", "line": 20}
    res = predictor.predict(finding)

    assert "score" in res
    assert 0.0 <= res["score"] <= 1.0
    assert res["severity"] in ["CRITICAL", "MEDIUM", "SAFE"]
    assert "confidence" in res


# 4. test_predict_batch
def test_predict_batch():
    predictor = RiskPredictor()
    findings = [
        {"file": "a.py", "algorithm": "RSA-2048", "severity": "CRITICAL"},
        {"file": "b.py", "algorithm": "AES-256", "severity": "SAFE"}
    ]
    preds = predictor.predict_batch(findings)
    assert len(preds) == 2
    assert preds[0]["score"] >= preds[1]["score"]


# 5. test_model_info_endpoint
def test_model_info_endpoint():
    response = client.get("/api/risk/model-info")
    assert response.status_code == 200
    data = response.json()
    assert "model_type" in data


# 6. test_prediction_has_explanation
def test_prediction_has_explanation():
    predictor = RiskPredictor()
    finding = {"file": "keys.pem", "algorithm": "RSA-4096", "severity": "CRITICAL"}
    res = predictor.predict(finding)

    assert "top_factors" in res
    assert isinstance(res["top_factors"], list)
    assert len(res["top_factors"]) >= 1
    factor = res["top_factors"][0]
    assert "feature" in factor
    assert "direction" in factor
