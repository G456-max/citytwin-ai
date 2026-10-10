"""
Unit Tests for Synthetic Dataset Generator (Phase C2)
Validates synthesis of 1,000 findings, statistical algorithm distribution,
explicit synthetic tagging, and balanced risk labels.
"""

from collections import Counter
from app.ml.dataset_builder import SyntheticDatasetGenerator
from app.ml.features import FeatureExtractor


# 1. test_generate_1000_findings
def test_generate_1000_findings():
    generator = SyntheticDatasetGenerator(seed=42)
    findings = generator.generate(n_samples=1000)
    assert len(findings) == 1000
    for f in findings:
        assert "algorithm" in f
        assert "file" in f
        assert "severity" in f


# 2. test_algorithm_distribution (roughly matches target weights)
def test_algorithm_distribution():
    generator = SyntheticDatasetGenerator(seed=42)
    findings = generator.generate(n_samples=2000, seed=123)
    counts = Counter(f["algorithm"] for f in findings)

    # RSA-2048 target weight: 25% (expect roughly 20% - 30%)
    rsa2048_freq = counts["RSA-2048"] / 2000.0
    assert 0.18 <= rsa2048_freq <= 0.32

    # AES-256 target weight: 20% (expect roughly 15% - 25%)
    aes256_freq = counts["AES-256"] / 2000.0
    assert 0.14 <= aes256_freq <= 0.26

    # MD5 target weight: 5% (expect roughly 2% - 8%)
    md5_freq = counts["MD5"] / 2000.0
    assert 0.02 <= md5_freq <= 0.08


# 3. test_metadata_says_synthetic
def test_metadata_says_synthetic():
    generator = SyntheticDatasetGenerator()
    findings = generator.generate(n_samples=50)
    for f in findings:
        assert f.get("dataset_type") == "SYNTHETIC"


# 4. test_labels_balance (both classes present)
def test_labels_balance():
    generator = SyntheticDatasetGenerator(seed=42)
    findings = generator.generate(n_samples=500)
    extractor = FeatureExtractor()
    labels = [extractor.extract_label(f) for f in findings]

    c = Counter(labels)
    assert 0 in c
    assert 1 in c
    # High risk should be roughly 65% (RSA+ECDSA+MD5+SHA1) vs 35% safe (AES+SHA256)
    ratio_class_1 = c[1] / float(len(labels))
    assert 0.50 <= ratio_class_1 <= 0.80
