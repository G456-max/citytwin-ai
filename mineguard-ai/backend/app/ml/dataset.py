"""
MineGuard AI - Dataset Preparation & Stratified Partitioning (Phase C1/C2)
Prepares feature matrices, extracts rule-based labels, and partitions
data into train/validation/test splits with stratification and small-sample safeguards.
"""

from typing import Dict, Any, List, Optional
import numpy as np
from sklearn.model_selection import train_test_split
import networkx as nx

from app.ml.features import FeatureExtractor, FEATURE_NAMES


class DataLabeler:
    """
    Documents label provenance, derivation logic, and research limitations.
    """

    @staticmethod
    def get_label_definition() -> Dict[str, Any]:
        """
        Returns full schema and honest limitation disclosure for risk labels.
        """
        return {
            "label_type": "Binary Classification (Quantum Vulnerability Exposure)",
            "classes": {
                0: "Low/Mitigated Risk (Safe algorithms or lower classical severity)",
                1: "High Quantum Risk (Broken by Shor's or weakened by Grover's algorithm with CRITICAL/HIGH severity)"
            },
            "derivation_rule": "Deterministic severity mapping: CRITICAL | HIGH -> 1; MEDIUM | LOW | SAFE -> 0",
            "provenance": "Rule-based synthesis from NIST FIPS 203/204/205 standards and CVSS cryptographic severity",
            "limitations": [
                "No real-world quantum computer cyberattack incident data currently exists globally.",
                "Labels represent theoretical cryptanalytic vulnerability rather than observed exploit telemetry.",
                "Downstream model predictions must be interpreted as compliance vulnerability scores, not empirical breach probabilities."
            ]
        }


class DatasetBuilder:
    """
    Builds structured training, validation, and test datasets from cryptographic findings.
    """

    def __init__(self, seed: int = 42, test_size: float = 0.2, val_size: float = 0.1):
        self.seed = seed
        self.test_size = test_size
        self.val_size = val_size

    def build(self, findings: List[Dict[str, Any]], graph: Optional[nx.DiGraph] = None) -> Dict[str, Any]:
        """
        Extracts features, applies stratified train/val/test splitting, and computes dataset metadata.
        Handles edge cases where total samples are small (< 20) or single-class.
        """
        extractor = FeatureExtractor(graph=graph)
        X, y, feature_names = extractor.transform(findings)

        n_samples = len(X)
        if n_samples == 0:
            empty = np.empty((0, len(feature_names)))
            return {
                "X_train": empty, "y_train": np.empty((0,)),
                "X_val": empty, "y_val": np.empty((0,)),
                "X_test": empty, "y_test": np.empty((0,)),
                "feature_names": feature_names,
                "metadata": {
                    "n_samples": 0, "n_features": len(feature_names),
                    "class_balance": {0: 0, 1: 0},
                    "split_sizes": {"train": 0, "val": 0, "test": 0}
                }
            }

        unique_labels, counts = np.unique(y, return_counts=True)
        class_balance = {int(k): int(v) for k, v in zip(unique_labels, counts)}

        # Safeguard for small or single-class datasets
        stratify_flag = y if (len(unique_labels) > 1 and min(counts) >= 2 and n_samples >= 10) else None

        if n_samples < 5:
            # Degenerate tiny sample
            return {
                "X_train": X, "y_train": y,
                "X_val": X, "y_val": y,
                "X_test": X, "y_test": y,
                "feature_names": feature_names,
                "metadata": {
                    "n_samples": n_samples,
                    "n_features": len(feature_names),
                    "class_balance": class_balance,
                    "split_sizes": {"train": n_samples, "val": n_samples, "test": n_samples},
                    "note": "Tiny sample size; replicated splits for pipeline continuity"
                }
            }

        # First split: (train + val) vs test
        X_train_val, X_test, y_train_val, y_test = train_test_split(
            X, y,
            test_size=self.test_size,
            random_state=self.seed,
            stratify=stratify_flag
        )

        # Second split: train vs val
        val_ratio = self.val_size / (1.0 - self.test_size)
        u_tv, c_tv = np.unique(y_train_val, return_counts=True)
        stratify_val = y_train_val if (len(u_tv) > 1 and min(c_tv) >= 2 and len(y_train_val) >= 6) else None

        X_train, X_val, y_train, y_val = train_test_split(
            X_train_val, y_train_val,
            test_size=val_ratio,
            random_state=self.seed,
            stratify=stratify_val
        )

        metadata = {
            "n_samples": int(n_samples),
            "n_features": len(feature_names),
            "class_balance": class_balance,
            "test_size": self.test_size,
            "val_size": self.val_size,
            "split_sizes": {
                "train": int(len(X_train)),
                "val": int(len(X_val)),
                "test": int(len(X_test))
            },
            "label_provenance": DataLabeler.get_label_definition()
        }

        return {
            "X_train": X_train,
            "y_train": y_train,
            "X_val": X_val,
            "y_val": y_val,
            "X_test": X_test,
            "y_test": y_test,
            "feature_names": feature_names,
            "metadata": metadata
        }
