"""
MineGuard AI - 25-Feature Engineering Pipeline (Phase C1)
Extracts multi-dimensional risk features across cryptographic parameters,
operational context, NIST PQC migration metrics, network dependency topology,
system context, and Mosca's theorem parameters.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set
import numpy as np
import networkx as nx

from app.engines.pqc_mapper import map_to_pqc, normalize_algorithm


# ============ FEATURE NAMES (25 FEATURES ACROSS 6 CATEGORIES) ============
FEATURE_NAMES: List[str] = [
    # 1. Cryptographic (6)
    "algorithm_vulnerability",
    "key_size_normalized",
    "quantum_threat_type",
    "is_asymmetric",
    "is_hash",
    "is_symmetric",

    # 2. Operational (6)
    "file_is_config",
    "file_is_code",
    "file_is_certificate",
    "line_density",
    "context_has_test",
    "context_has_prod",

    # 3. PQC Mapping (5)
    "has_pqc_replacement",
    "migration_complexity_score",
    "migration_effort_normalized",
    "urgency_score",
    "nist_standard_priority",

    # 4. Dependency (4)
    "in_degree",
    "out_degree",
    "is_cascade_trigger",
    "centrality_score",

    # 5. System Context (3)
    "criticality_score",
    "exposure_score",
    "data_lifetime_normalized",

    # 6. Mosca Theorem (1)
    "mosca_gap_normalized"
]


# ============ SCORE MAPS ============
SEVERITY_SCORES: Dict[str, float] = {
    "CRITICAL": 1.0,
    "HIGH": 0.75,
    "MEDIUM": 0.5,
    "LOW": 0.25,
    "SAFE": 0.0
}

COMPLEXITY_SCORES: Dict[str, float] = {
    "CRITICAL": 1.0,
    "HIGH": 0.8,
    "MEDIUM": 0.5,
    "LOW": 0.2,
    "TRIVIAL": 0.0
}

URGENCY_SCORES: Dict[str, float] = {
    "CRITICAL": 1.0,
    "HIGH": 0.75,
    "MEDIUM": 0.5,
    "LOW": 0.25,
    "NONE": 0.0
}

CRITICALITY_SCORES: Dict[str, float] = {
    "CRITICAL": 1.0,
    "HIGH": 0.75,
    "MEDIUM": 0.5,
    "LOW": 0.25,
    "NONE": 0.0
}

EXPOSURE_SCORES: Dict[str, float] = {
    "EXTERNAL": 1.0,
    "PERIMETER": 0.75,
    "INTERNAL": 0.4,
    "AIR-GAPPED": 0.1,
    "ISOLATED": 0.1
}


# ============ QUANTUM THREAT SETS ============
SHOR_BROKEN: Set[str] = {
    "RSA", "RSA-1024", "RSA-2048", "RSA-3072", "RSA-4096",
    "ECDSA", "ECDSA-P256", "ECDSA-P384", "ECDH",
    "DSA", "DH", "DIFFIE-HELLMAN", "ECC"
}

GROVER_WEAKENED: Set[str] = {
    "MD5", "SHA-1", "SHA1", "AES-128"
}


# ============ FEATURE EXTRACTOR CLASS ============
class FeatureExtractor:
    """
    Transforms raw cryptographic findings and optional dependency graphs
    into normalized 25-dimensional feature vectors for risk modeling.
    """

    def __init__(self, graph: Optional[nx.DiGraph] = None):
        self.graph = graph
        self.graph_stats: Dict[str, Dict[str, float]] = {}
        if self.graph is not None:
            self._compute_graph_stats()

    def _compute_graph_stats(self) -> None:
        """Pre-computes degree and betweenness centrality metrics across the dependency graph."""
        if not self.graph or len(self.graph.nodes) == 0:
            return

        try:
            betweenness = nx.betweenness_centrality(self.graph)
        except Exception:
            betweenness = {n: 0.0 for n in self.graph.nodes}

        max_in = max([d for _, d in self.graph.in_degree()], default=1) or 1
        max_out = max([d for _, d in self.graph.out_degree()], default=1) or 1

        for node in self.graph.nodes:
            self.graph_stats[str(node)] = {
                "in_degree": float(self.graph.in_degree(node)) / float(max_in),
                "out_degree": float(self.graph.out_degree(node)) / float(max_out),
                "centrality": float(betweenness.get(node, 0.0))
            }

    def transform(self, findings: List[Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Transforms a batch of findings into feature matrix X, label array y, and feature names.
        """
        if not findings:
            return np.empty((0, len(FEATURE_NAMES))), np.empty((0,)), FEATURE_NAMES

        X_list = [self.extract_features(f) for f in findings]
        y_list = [self.extract_label(f) for f in findings]

        X = np.array(X_list, dtype=np.float64)
        y = np.array(y_list, dtype=np.int64)

        return X, y, FEATURE_NAMES

    def extract_label(self, finding: Dict[str, Any]) -> int:
        """
        Derives ground-truth risk classification label (0 or 1).
        Rule-based heuristic: CRITICAL or HIGH severity = 1 (High Risk),
        MEDIUM, LOW, or SAFE = 0 (Acceptable / Low Risk).
        """
        severity = str(finding.get("severity", "MEDIUM")).upper()
        if severity in {"CRITICAL", "HIGH"}:
            return 1
        return 0

    def extract_features(self, finding: Dict[str, Any]) -> List[float]:
        """Extracts the exact 25-feature vector for a single finding."""
        algo = normalize_algorithm(str(finding.get("algorithm", "UNKNOWN")))
        pqc = finding.get("pqc") or map_to_pqc(algo)
        file_path = str(finding.get("file", ""))
        context = str(finding.get("context", ""))
        line = int(finding.get("line", 1))
        key_size = finding.get("key_size")

        return [
            # 1. Cryptographic (6)
            self._f_algorithm_vulnerability(finding, algo),
            self._f_key_size_normalized(key_size, algo),
            self._f_quantum_threat_type(algo),
            self._f_is_asymmetric(algo),
            self._f_is_hash(algo),
            self._f_is_symmetric(algo),

            # 2. Operational (6)
            self._f_file_is_config(file_path),
            self._f_file_is_code(file_path),
            self._f_file_is_certificate(file_path),
            self._f_line_density(line),
            self._f_context_has_test(file_path, context),
            self._f_context_has_prod(file_path, context),

            # 3. PQC Mapping (5)
            self._f_has_pqc_replacement(pqc),
            self._f_migration_complexity_score(pqc),
            self._f_migration_effort_normalized(pqc),
            self._f_urgency_score(pqc),
            self._f_nist_standard_priority(pqc),

            # 4. Dependency (4)
            self._f_in_degree(file_path),
            self._f_out_degree(file_path),
            self._f_is_cascade_trigger(file_path, pqc),
            self._f_centrality_score(file_path),

            # 5. System Context (3)
            self._f_criticality_score(finding, file_path),
            self._f_exposure_score(finding, file_path),
            self._f_data_lifetime_normalized(finding),

            # 6. Mosca Theorem (1)
            self._f_mosca_gap_normalized(finding, pqc)
        ]

    # ---- 1. Cryptographic Features ----
    def _f_algorithm_vulnerability(self, finding: Dict[str, Any], algo: str) -> float:
        sev = str(finding.get("severity", "")).upper()
        if sev in SEVERITY_SCORES:
            return SEVERITY_SCORES[sev]
        if algo in SHOR_BROKEN:
            return 1.0
        if algo in GROVER_WEAKENED:
            return 0.75
        if "AES-256" in algo or "SHA-256" in algo or "ML-" in algo:
            return 0.0
        return 0.5

    def _f_key_size_normalized(self, key_size: Optional[int], algo: str) -> float:
        if key_size:
            return float(min(max(key_size, 0) / 4096.0, 1.0))
        if "2048" in algo:
            return 2048.0 / 4096.0
        if "4096" in algo:
            return 1.0
        if "256" in algo:
            return 256.0 / 4096.0
        return 0.0

    def _f_quantum_threat_type(self, algo: str) -> float:
        if algo in SHOR_BROKEN:
            return 1.0   # Shor's polynomial factor / discrete log
        if algo in GROVER_WEAKENED:
            return 0.5   # Grover's quadratic speedup
        return 0.0       # Quantum resistant

    def _f_is_asymmetric(self, algo: str) -> float:
        return 1.0 if algo in SHOR_BROKEN or any(k in algo for k in ["RSA", "ECDSA", "ECDH", "DSA", "DH"]) else 0.0

    def _f_is_hash(self, algo: str) -> float:
        return 1.0 if any(k in algo for k in ["MD5", "SHA-1", "SHA1", "SHA-256", "SHA-3", "SHA"]) else 0.0

    def _f_is_symmetric(self, algo: str) -> float:
        return 1.0 if any(k in algo for k in ["AES", "DES", "CHACHA"]) else 0.0

    # ---- 2. Operational Features ----
    def _f_file_is_config(self, file_path: str) -> float:
        ext = Path(file_path).suffix.lower()
        return 1.0 if ext in {".yaml", ".yml", ".json", ".toml", ".ini", ".conf", ".env", ".cfg", ".xml", ".properties"} else 0.0

    def _f_file_is_code(self, file_path: str) -> float:
        ext = Path(file_path).suffix.lower()
        return 1.0 if ext in {".py", ".pyw", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rs", ".c", ".cpp", ".cs"} else 0.0

    def _f_file_is_certificate(self, file_path: str) -> float:
        ext = Path(file_path).suffix.lower()
        return 1.0 if ext in {".pem", ".crt", ".cer", ".key", ".p12"} else 0.0

    def _f_line_density(self, line: int) -> float:
        return float(min(max(line, 1) / 1000.0, 1.0))

    def _f_context_has_test(self, file_path: str, context: str) -> float:
        combined = f"{file_path} {context}".lower()
        return 1.0 if any(k in combined for k in ["test", "mock", "fixture", "spec", "stub"]) else 0.0

    def _f_context_has_prod(self, file_path: str, context: str) -> float:
        combined = f"{file_path} {context}".lower()
        return 1.0 if any(k in combined for k in ["prod", "production", "main", "deploy", "scada", "plc", "sensor", "haul"]) else 0.0

    # ---- 3. PQC Mapping Features ----
    def _f_has_pqc_replacement(self, pqc: Dict[str, Any]) -> float:
        return 1.0 if (pqc.get("kem") or pqc.get("sig") or pqc.get("symmetric") or pqc.get("hash")) else 0.0

    def _f_migration_complexity_score(self, pqc: Dict[str, Any]) -> float:
        c = str(pqc.get("complexity", "TRIVIAL")).upper()
        return COMPLEXITY_SCORES.get(c, 0.0)

    def _f_migration_effort_normalized(self, pqc: Dict[str, Any]) -> float:
        weeks = float(pqc.get("effort_weeks", 0))
        return min(weeks / 12.0, 1.0)

    def _f_urgency_score(self, pqc: Dict[str, Any]) -> float:
        u = str(pqc.get("urgency", "NONE")).upper()
        return URGENCY_SCORES.get(u, 0.0)

    def _f_nist_standard_priority(self, pqc: Dict[str, Any]) -> float:
        std = str(pqc.get("standard", ""))
        if "FIPS 203" in std or "FIPS 204" in std:
            return 1.0
        if "FIPS 205" in std:
            return 0.8
        return 0.0

    # ---- 4. Dependency Features ----
    def _f_in_degree(self, file_path: str) -> float:
        stats = self.graph_stats.get(file_path) or self.graph_stats.get(Path(file_path).stem, {})
        return stats.get("in_degree", 0.1)

    def _f_out_degree(self, file_path: str) -> float:
        stats = self.graph_stats.get(file_path) or self.graph_stats.get(Path(file_path).stem, {})
        return stats.get("out_degree", 0.1)

    def _f_is_cascade_trigger(self, file_path: str, pqc: Dict[str, Any]) -> float:
        # Critical nodes or root certificate/SCADA triggers
        lower = file_path.lower()
        if any(k in lower for k in ["root", "ca", "scada", "gateway", "auth", "master"]):
            return 1.0 if not pqc.get("quantum_safe", True) else 0.0
        stats = self.graph_stats.get(file_path) or self.graph_stats.get(Path(file_path).stem, {})
        return 1.0 if stats.get("centrality", 0.0) >= 0.2 else 0.0

    def _f_centrality_score(self, file_path: str) -> float:
        stats = self.graph_stats.get(file_path) or self.graph_stats.get(Path(file_path).stem, {})
        return stats.get("centrality", 0.1)

    # ---- 5. System Context Features ----
    def _f_criticality_score(self, finding: Dict[str, Any], file_path: str) -> float:
        if "criticality" in finding:
            return CRITICALITY_SCORES.get(str(finding["criticality"]).upper(), 0.5)
        lower = file_path.lower()
        if any(k in lower for k in ["scada", "plc", "ventilation", "haul", "safety", "auth"]):
            return 1.0
        if any(k in lower for k in ["db", "telemetry", "mesh", "sensor"]):
            return 0.75
        return 0.4

    def _f_exposure_score(self, finding: Dict[str, Any], file_path: str) -> float:
        if "exposure" in finding:
            return EXPOSURE_SCORES.get(str(finding["exposure"]).upper(), 0.4)
        lower = file_path.lower()
        if any(k in lower for k in ["gateway", "portal", "cloud", "api", "external"]):
            return 1.0
        if any(k in lower for k in ["bridge", "mesh", "fleet", "perimeter"]):
            return 0.75
        return 0.3

    def _f_data_lifetime_normalized(self, finding: Dict[str, Any]) -> float:
        # Mining environmental & safety compliance data requires 10-30 years retention
        lifetime_years = finding.get("data_lifetime_years", 15.0)
        try:
            val = float(lifetime_years)
        except (ValueError, TypeError):
            val = 15.0
        return min(max(val, 1.0) / 30.0, 1.0)

    # ---- 6. Mosca Theorem Feature ----
    def _f_mosca_gap_normalized(self, finding: Dict[str, Any], pqc: Dict[str, Any]) -> float:
        """
        Mosca's Theorem: If (Security Shelf-Life X + Migration Time Y) > Quantum Collapse Time Z,
        the infrastructure is in an active quantum exposure state.
        Default parameters for mining OT:
          X (Data shelf-life) ~ 15 years
          Y (Migration time) ~ 3 years
          Z (Time to Q-Day: 2029 - 2026) ~ 3 years
          Gap = (15 + 3) - 3 = 15 years -> Highly Exposed.
        """
        if pqc.get("quantum_safe"):
            return 0.0

        x_years = float(finding.get("shelf_life_years", 10.0))
        y_years = float(pqc.get("effort_weeks", 6)) / 52.0 + 2.0  # planning buffer
        z_years = max(float(finding.get("q_day_years", 3.0)), 1.0)

        gap = (x_years + y_years) - z_years
        return min(max(gap / 20.0, 0.0), 1.0)
