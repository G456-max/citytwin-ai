"""
MineGuard AI - Model Card & Responsible AI Documentation Generator (Phase C7)
Generates structured Model Cards documenting model architecture, training data provenance,
evaluation benchmarks, ethical considerations, and explicit operational limitations.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone


class ModelCard:
    """
    Generates GitHub Flavored Markdown Model Cards for regulatory compliance and auditability.
    """

    def __init__(self, metadata: Optional[Dict[str, Any]] = None):
        self.metadata = metadata or {}

    def generate_markdown(self) -> str:
        """Assembles comprehensive Model Card in markdown format."""
        model_type = self.metadata.get("model_type", "LogisticRegression (Balanced)")
        version = self.metadata.get("version", "1.0.0")
        trained_at = self.metadata.get("trained_at", datetime.now(timezone.utc).isoformat())
        n_samples = self.metadata.get("n_samples", "1000 (Synthetic)")
        metrics = self.metadata.get("metrics", {}).get("test", {})

        acc = metrics.get("accuracy", "N/A")
        prec = metrics.get("precision", "N/A")
        rec = metrics.get("recall", "N/A")
        f1 = metrics.get("f1", "N/A")
        auc = metrics.get("roc_auc", "N/A")

        return f"""# MineGuard AI — Model Card: {model_type}

> **Tagline:** "Predict the risk. Trace the impact. Plan the migration."

---

## 1. Model Details
- **Architecture / Type:** {model_type}
- **Version:** {version}
- **Trained At:** {trained_at}
- **Framework:** scikit-learn (with optional XGBoost & SHAP)
- **Primary Task:** Binary Quantum Cryptographic Vulnerability Exposure Classification

---

## 2. Intended Use
- **Primary Intended Use:** Prioritizing cryptographic migration pathways for safety-critical mining and operational technology (OT) systems.
- **Intended Users:** Mining cybersecurity engineers, industrial SCADA architects, and post-quantum compliance auditors.
- **Out-of-Scope Use:** Automated mission-critical shutdowns without human supervisory approval.

---

## 3. Training Data Provenance
- **Dataset Size:** {n_samples} samples
- **Data Source:** Statistical simulation calibrated to mining operational technology systems (SCADA, PLC, telemetry networks).
- **Labeling Mechanism:** Rule-based derivation from NIST FIPS 203/204/205 quantum vulnerability guidelines.
- **Ground Truth Note:** Labels reflect algorithmic vulnerability to Shor's and Grover's algorithms, not observed historical attack logs.

---

## 4. Input Features (25 Features across 6 Domains)
1. **Cryptographic:** `algorithm_vulnerability`, `key_size_normalized`, `quantum_threat_type`, `is_asymmetric`, `is_hash`, `is_symmetric`
2. **Operational:** `file_is_config`, `file_is_code`, `file_is_certificate`, `line_density`, `context_has_test`, `context_has_prod`
3. **PQC Mapping:** `has_pqc_replacement`, `migration_complexity_score`, `migration_effort_normalized`, `urgency_score`, `nist_standard_priority`
4. **Dependency:** `in_degree`, `out_degree`, `is_cascade_trigger`, `centrality_score`
5. **System Context:** `criticality_score`, `exposure_score`, `data_lifetime_normalized`
6. **Mosca's Theorem:** `mosca_gap_normalized`

---

## 5. Measured Evaluation Metrics
- **Accuracy:** {acc}
- **Precision (Weighted):** {prec}
- **Recall (Weighted):** {rec}
- **F1 Score (Weighted):** {f1}
- **ROC-AUC:** {auc}

*(Note: Metrics reflect actual evaluation on stratified test partitions. No synthetic perfection claimed.)*

---

## 6. Limitations & Caveats
- **Lack of Empirical Incident Data:** No real-world cryptanalytically relevant quantum computers exist today; consequently, zero empirical quantum cyberattack incident datasets exist worldwide.
- **Code Parsing Bounds:** Dynamic imports or obfuscated algorithm initializations cannot be statically inferred.
- **Environmental Drift:** Operational assumptions (data shelf-life, Q-Day horizon) vary by jurisdiction and mining sector.

---

## 7. Ethical & Responsible AI Considerations
- Models are designed for proactive defense and migration planning.
- Predictions include explainability attributions so operators understand why an asset was classified as high risk.
- Human-in-the-loop validation is required before executing code migrations.
"""
