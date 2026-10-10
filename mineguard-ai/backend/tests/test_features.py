"""
Unit Tests for 25-Feature Engineering and Dataset Pipeline (Phases C1 & C2)
Validates feature counts, numeric types, bounds, deterministic binary labeling,
vulnerability differentiation, and stratified partitioning.
"""

import pytest
import numpy as np

from app.ml.features import FeatureExtractor, FEATURE_NAMES
from app.ml.dataset import DatasetBuilder, DataLabeler


@pytest.fixture
def sample_findings():
    return [
        {
            "file": "auth/keys.pem",
            "line": 12,
            "algorithm": "RSA-2048",
            "severity": "CRITICAL",
            "key_size": 2048,
            "context": "root_ca = load_key()"
        },
        {
            "file": "crypto/cipher.py",
            "line": 150,
            "algorithm": "AES-256",
            "severity": "SAFE",
            "key_size": 256,
            "context": "cipher = AES.new()"
        },
        {
            "file": "telemetry/db.py",
            "line": 45,
            "algorithm": "MD5",
            "severity": "HIGH",
            "key_size": None,
            "context": "h = hashlib.md5()"
        },
        {
            "file": "scada/plc.c",
            "line": 80,
            "algorithm": "ECDSA",
            "severity": "CRITICAL",
            "key_size": 256,
            "context": "sign = ecdsa_sign()"
        }
    ]


# 1. test_feature_count (25 features)
def test_feature_count(sample_findings):
    extractor = FeatureExtractor()
    assert len(FEATURE_NAMES) == 25
    feats = extractor.extract_features(sample_findings[0])
    assert len(feats) == 25


# 2. test_all_features_numeric
def test_all_features_numeric(sample_findings):
    extractor = FeatureExtractor()
    for f in sample_findings:
        feats = extractor.extract_features(f)
        for val in feats:
            assert isinstance(val, (int, float, np.floating, np.integer))
            assert not np.isnan(val)
            assert not np.isinf(val)


# 3. test_feature_ranges (all in [0, 1] or bounded)
def test_feature_ranges(sample_findings):
    extractor = FeatureExtractor()
    for f in sample_findings:
        feats = extractor.extract_features(f)
        for idx, val in enumerate(feats):
            feat_name = FEATURE_NAMES[idx]
            assert 0.0 <= val <= 1.0, f"Feature {feat_name} out of bounds: {val}"


# 4. test_labels_are_binary
def test_labels_are_binary(sample_findings):
    extractor = FeatureExtractor()
    for f in sample_findings:
        label = extractor.extract_label(f)
        assert label in {0, 1}


# 5. test_high_severity_gets_label_1
def test_high_severity_gets_label_1(sample_findings):
    extractor = FeatureExtractor()
    crit_finding = sample_findings[0]  # CRITICAL
    high_finding = sample_findings[2]  # HIGH
    assert extractor.extract_label(crit_finding) == 1
    assert extractor.extract_label(high_finding) == 1


# 6. test_safe_gets_label_0
def test_safe_gets_label_0(sample_findings):
    extractor = FeatureExtractor()
    safe_finding = sample_findings[1]  # SAFE
    assert extractor.extract_label(safe_finding) == 0


# 7. test_rsa_has_high_vulnerability
def test_rsa_has_high_vulnerability():
    extractor = FeatureExtractor()
    finding = {"file": "ca.pem", "line": 1, "algorithm": "RSA-2048", "severity": "CRITICAL"}
    feats = extractor.extract_features(finding)
    idx = FEATURE_NAMES.index("algorithm_vulnerability")
    assert feats[idx] == 1.0


# 8. test_aes256_has_zero_vulnerability
def test_aes256_has_zero_vulnerability():
    extractor = FeatureExtractor()
    finding = {"file": "sec.py", "line": 10, "algorithm": "AES-256", "severity": "SAFE"}
    feats = extractor.extract_features(finding)
    idx = FEATURE_NAMES.index("algorithm_vulnerability")
    assert feats[idx] == 0.0


# 9. test_dataset_builder_splits
def test_dataset_builder_splits(sample_findings):
    # Repeat findings to have sufficient data for split
    large_set = sample_findings * 10  # 40 items
    builder = DatasetBuilder(seed=42, test_size=0.2, val_size=0.1)
    dataset = builder.build(large_set)

    assert "X_train" in dataset
    assert "X_val" in dataset
    assert "X_test" in dataset
    assert len(dataset["X_train"]) > 0
    assert len(dataset["X_val"]) > 0
    assert len(dataset["X_test"]) > 0
    total = len(dataset["X_train"]) + len(dataset["X_val"]) + len(dataset["X_test"])
    assert total == len(large_set)


# 10. test_dataset_metadata
def test_dataset_metadata(sample_findings):
    large_set = sample_findings * 8
    builder = DatasetBuilder()
    data = builder.build(large_set)
    meta = data["metadata"]

    assert meta["n_samples"] == len(large_set)
    assert meta["n_features"] == 25
    assert "class_balance" in meta
    assert meta["class_balance"][0] > 0
    assert meta["class_balance"][1] > 0


# 11. test_labeler_documents_limitations
def test_labeler_documents_limitations():
    doc = DataLabeler.get_label_definition()
    assert "limitations" in doc
    assert len(doc["limitations"]) >= 2
    assert "provenance" in doc
    assert any("quantum" in s.lower() for s in doc["limitations"])
