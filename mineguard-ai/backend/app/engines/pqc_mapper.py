"""
MineGuard AI - NIST Post-Quantum Cryptography (PQC) Mapping Engine (Phase B2)
Maps classical and quantum-vulnerable cryptographic algorithms to standardized
NIST FIPS 203 (ML-KEM), FIPS 204 (ML-DSA), and FIPS 205 (SLH-DSA) replacements.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
import re


# ============ 1. PQC STANDARDS & COMPLEXITY ENUMS ============
class PQCStandard(str, Enum):
    FIPS_203 = "FIPS 203 (ML-KEM)"
    FIPS_204 = "FIPS 204 (ML-DSA)"
    FIPS_205 = "FIPS 205 (SLH-DSA)"
    NONE = "No migration needed"


class MigrationComplexity(str, Enum):
    TRIVIAL = "TRIVIAL"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# ============ 2. PQC MAPPING TABLE ============
PQC_MAPPING: Dict[str, Dict[str, Any]] = {
    # RSA Variants
    "RSA-1024": {
        "kem": "ML-KEM-768",
        "sig": "ML-DSA-65",
        "alt_sig": "SLH-DSA-SHA2-128s",
        "hash": None,
        "symmetric": None,
        "standard": PQCStandard.FIPS_203.value,
        "complexity": MigrationComplexity.HIGH.value,
        "effort_weeks": 8,
        "reason": "Vulnerable to Shor's algorithm; immediate risk due to sub-standard key length",
        "urgency": "CRITICAL",
        "quantum_safe": False
    },
    "RSA-2048": {
        "kem": "ML-KEM-768",
        "sig": "ML-DSA-65",
        "alt_sig": "SLH-DSA-SHA2-128s",
        "hash": None,
        "symmetric": None,
        "standard": PQCStandard.FIPS_203.value,
        "complexity": MigrationComplexity.HIGH.value,
        "effort_weeks": 6,
        "reason": "Vulnerable to Shor's algorithm (period finding polynomial-time factor)",
        "urgency": "CRITICAL",
        "quantum_safe": False
    },
    "RSA-3072": {
        "kem": "ML-KEM-1024",
        "sig": "ML-DSA-87",
        "alt_sig": "SLH-DSA-SHA2-192s",
        "hash": None,
        "symmetric": None,
        "standard": PQCStandard.FIPS_203.value,
        "complexity": MigrationComplexity.MEDIUM.value,
        "effort_weeks": 6,
        "reason": "Vulnerable to Shor's algorithm despite larger classical key size",
        "urgency": "CRITICAL",
        "quantum_safe": False
    },
    "RSA-4096": {
        "kem": "ML-KEM-1024",
        "sig": "ML-DSA-87",
        "alt_sig": "SLH-DSA-SHA2-256s",
        "hash": None,
        "symmetric": None,
        "standard": PQCStandard.FIPS_203.value,
        "complexity": MigrationComplexity.MEDIUM.value,
        "effort_weeks": 6,
        "reason": "Vulnerable to Shor's algorithm; larger key size does not protect against Q-Day",
        "urgency": "CRITICAL",
        "quantum_safe": False
    },
    "RSA": {
        "kem": "ML-KEM-768",
        "sig": "ML-DSA-65",
        "alt_sig": "SLH-DSA-SHA2-128s",
        "hash": None,
        "symmetric": None,
        "standard": PQCStandard.FIPS_203.value,
        "complexity": MigrationComplexity.HIGH.value,
        "effort_weeks": 6,
        "reason": "Vulnerable to Shor's algorithm (period finding)",
        "urgency": "CRITICAL",
        "quantum_safe": False
    },

    # Elliptic Curve Digital Signature
    "ECDSA-P256": {
        "kem": None,
        "sig": "ML-DSA-44",
        "alt_sig": "SLH-DSA-SHA2-128s",
        "hash": None,
        "symmetric": None,
        "standard": PQCStandard.FIPS_204.value,
        "complexity": MigrationComplexity.HIGH.value,
        "effort_weeks": 6,
        "reason": "Discrete logarithm broken by Shor's algorithm",
        "urgency": "CRITICAL",
        "quantum_safe": False
    },
    "ECDSA-P384": {
        "kem": None,
        "sig": "ML-DSA-65",
        "alt_sig": "SLH-DSA-SHA2-192s",
        "hash": None,
        "symmetric": None,
        "standard": PQCStandard.FIPS_204.value,
        "complexity": MigrationComplexity.HIGH.value,
        "effort_weeks": 6,
        "reason": "Discrete logarithm broken by Shor's algorithm",
        "urgency": "CRITICAL",
        "quantum_safe": False
    },
    "ECDSA": {
        "kem": None,
        "sig": "ML-DSA-44",
        "alt_sig": "SLH-DSA-SHA2-128s",
        "hash": None,
        "symmetric": None,
        "standard": PQCStandard.FIPS_204.value,
        "complexity": MigrationComplexity.HIGH.value,
        "effort_weeks": 6,
        "reason": "Discrete logarithm broken by Shor's algorithm",
        "urgency": "CRITICAL",
        "quantum_safe": False
    },

    # Elliptic Curve Diffie-Hellman & Generic ECC
    "ECDH": {
        "kem": "ML-KEM-768",
        "sig": None,
        "alt_sig": None,
        "hash": None,
        "symmetric": None,
        "standard": PQCStandard.FIPS_203.value,
        "complexity": MigrationComplexity.HIGH.value,
        "effort_weeks": 8,
        "reason": "ECDH key agreement vulnerable to quantum discrete log attacks",
        "urgency": "CRITICAL",
        "quantum_safe": False
    },
    "ECC": {
        "kem": "ML-KEM-768",
        "sig": "ML-DSA-65",
        "alt_sig": "SLH-DSA-SHA2-128s",
        "hash": None,
        "symmetric": None,
        "standard": f"{PQCStandard.FIPS_203.value} / {PQCStandard.FIPS_204.value}",
        "complexity": MigrationComplexity.HIGH.value,
        "effort_weeks": 8,
        "reason": "Elliptic curve cryptography vulnerable to Shor's algorithm",
        "urgency": "CRITICAL",
        "quantum_safe": False
    },

    # Classical DSA / DH
    "DSA": {
        "kem": None,
        "sig": "ML-DSA-44",
        "alt_sig": "SLH-DSA-SHA2-128s",
        "hash": None,
        "symmetric": None,
        "standard": PQCStandard.FIPS_204.value,
        "complexity": MigrationComplexity.MEDIUM.value,
        "effort_weeks": 4,
        "reason": "Discrete log broken in polynomial time by Shor's algorithm",
        "urgency": "CRITICAL",
        "quantum_safe": False
    },
    "DH": {
        "kem": "ML-KEM-768",
        "sig": None,
        "alt_sig": None,
        "hash": None,
        "symmetric": None,
        "standard": PQCStandard.FIPS_203.value,
        "complexity": MigrationComplexity.HIGH.value,
        "effort_weeks": 8,
        "reason": "Diffie-Hellman key exchange broken by quantum discrete log",
        "urgency": "CRITICAL",
        "quantum_safe": False
    },
    "DIFFIE-HELLMAN": {
        "kem": "ML-KEM-768",
        "sig": None,
        "alt_sig": None,
        "hash": None,
        "symmetric": None,
        "standard": PQCStandard.FIPS_203.value,
        "complexity": MigrationComplexity.HIGH.value,
        "effort_weeks": 8,
        "reason": "Diffie-Hellman key exchange broken by quantum discrete log",
        "urgency": "CRITICAL",
        "quantum_safe": False
    },

    # Hash Functions
    "MD5": {
        "kem": None,
        "sig": None,
        "alt_sig": None,
        "hash": "SHA-3-256",
        "symmetric": None,
        "standard": PQCStandard.NONE.value,
        "complexity": MigrationComplexity.LOW.value,
        "effort_weeks": 2,
        "reason": "Classical collision weakness compounded by Grover quadratic search speedup",
        "urgency": "HIGH",
        "quantum_safe": False
    },
    "SHA-1": {
        "kem": None,
        "sig": None,
        "alt_sig": None,
        "hash": "SHA-3-256",
        "symmetric": None,
        "standard": PQCStandard.NONE.value,
        "complexity": MigrationComplexity.LOW.value,
        "effort_weeks": 2,
        "reason": "Classical collision weaknesses accelerated by quantum Grover search",
        "urgency": "HIGH",
        "quantum_safe": False
    },

    # Symmetric Key Ciphers
    "AES-128": {
        "kem": None,
        "sig": None,
        "alt_sig": None,
        "hash": None,
        "symmetric": "AES-256",
        "standard": PQCStandard.NONE.value,
        "complexity": MigrationComplexity.TRIVIAL.value,
        "effort_weeks": 1,
        "reason": "Grover's algorithm reduces effective security margin from 128 to 64 bits",
        "urgency": "MEDIUM",
        "quantum_safe": False
    },
    "AES-256": {
        "kem": None,
        "sig": None,
        "alt_sig": None,
        "hash": None,
        "symmetric": "AES-256",
        "standard": PQCStandard.NONE.value,
        "complexity": MigrationComplexity.TRIVIAL.value,
        "effort_weeks": 0,
        "reason": "Maintains 128 bits of security against Grover's algorithm (NIST compliant)",
        "urgency": "NONE",
        "quantum_safe": True
    },

    # Already Quantum-Safe Hashes
    "SHA-256": {
        "kem": None,
        "sig": None,
        "alt_sig": None,
        "hash": "SHA-256",
        "symmetric": None,
        "standard": PQCStandard.NONE.value,
        "complexity": MigrationComplexity.TRIVIAL.value,
        "effort_weeks": 0,
        "reason": "Collision resistance remains quantum safe (128-bit quantum security)",
        "urgency": "NONE",
        "quantum_safe": True
    },
    "SHA-3": {
        "kem": None,
        "sig": None,
        "alt_sig": None,
        "hash": "SHA-3-256",
        "symmetric": None,
        "standard": PQCStandard.NONE.value,
        "complexity": MigrationComplexity.TRIVIAL.value,
        "effort_weeks": 0,
        "reason": "NIST Keccak standard, inherently quantum resistant",
        "urgency": "NONE",
        "quantum_safe": True
    },

    # Standardized PQC Algorithms (Native FIPS)
    "ML-KEM": {
        "kem": "ML-KEM-768",
        "sig": None,
        "alt_sig": None,
        "hash": None,
        "symmetric": None,
        "standard": PQCStandard.FIPS_203.value,
        "complexity": MigrationComplexity.TRIVIAL.value,
        "effort_weeks": 0,
        "reason": "Standardized NIST FIPS 203 lattice-based key encapsulation mechanism",
        "urgency": "NONE",
        "quantum_safe": True
    },
    "ML-DSA": {
        "kem": None,
        "sig": "ML-DSA-65",
        "alt_sig": None,
        "hash": None,
        "symmetric": None,
        "standard": PQCStandard.FIPS_204.value,
        "complexity": MigrationComplexity.TRIVIAL.value,
        "effort_weeks": 0,
        "reason": "Standardized NIST FIPS 204 lattice-based digital signature algorithm",
        "urgency": "NONE",
        "quantum_safe": True
    },
    "SLH-DSA": {
        "kem": None,
        "sig": "SLH-DSA-SHA2-128s",
        "alt_sig": None,
        "hash": None,
        "symmetric": None,
        "standard": PQCStandard.FIPS_205.value,
        "complexity": MigrationComplexity.TRIVIAL.value,
        "effort_weeks": 0,
        "reason": "Standardized NIST FIPS 205 stateless hash-based digital signature standard",
        "urgency": "NONE",
        "quantum_safe": True
    }
}


# ============ 3. NORMALIZATION UTILITY ============
def normalize_algorithm(algorithm: str) -> str:
    """
    Normalizes arbitrary algorithm naming variants to standardized PQC table keys.
    Examples:
      - 'rsa' -> 'RSA-2048'
      - 'RSA2048' -> 'RSA-2048'
      - 'prime256v1' -> 'ECDSA-P256'
      - 'sha1' -> 'SHA-1'
    """
    if not algorithm:
        return "UNKNOWN"

    raw = algorithm.strip()
    upper = raw.upper()

    # Exact key match
    if upper in PQC_MAPPING:
        return upper

    # RSA variations
    rsa_match = re.search(r"RSA[-_]?(\d{3,4})", upper)
    if rsa_match:
        return f"RSA-{rsa_match.group(1)}"
    if upper == "RSA" or upper.startswith("RSA"):
        return "RSA-2048"

    # Curves & ECDSA
    if any(k in upper for k in ["PRIME256V1", "SECP256K1", "P256", "P-256", "SECP256R1"]):
        return "ECDSA-P256"
    if any(k in upper for k in ["SECP384R1", "P384", "P-384"]):
        return "ECDSA-P384"
    if "ECDSA" in upper:
        return "ECDSA"
    if "ECDH" in upper or "X25519" in upper or "X448" in upper:
        return "ECDH"
    if "ECC" in upper:
        return "ECC"

    # Diffie-Hellman
    if "DIFFIE" in upper or upper == "DH" or upper.startswith("DH-"):
        return "DH"
    if "DSA" in upper:
        return "DSA"

    # Hashes
    if "MD5" in upper:
        return "MD5"
    if any(k in upper for k in ["SHA1", "SHA-1"]):
        return "SHA-1"
    if "SHA256" in upper or "SHA-256" in upper:
        return "SHA-256"
    if "SHA3" in upper or "SHA-3" in upper:
        return "SHA-3"

    # Symmetric
    if "AES-128" in upper or "AES128" in upper:
        return "AES-128"
    if "AES-256" in upper or "AES256" in upper or upper == "AES":
        return "AES-256"

    # PQC
    if "KYBER" in upper or "ML-KEM" in upper or "MLKEM" in upper:
        return "ML-KEM"
    if "DILITHIUM" in upper or "ML-DSA" in upper or "MLDSA" in upper:
        return "ML-DSA"
    if "SPHINCS" in upper or "SLH-DSA" in upper or "SLHDSA" in upper:
        return "SLH-DSA"

    return upper


# ============ 4. MAPPING FUNCTION ============
def map_to_pqc(algorithm: str) -> Dict[str, Any]:
    """
    Returns full PQC migration details for a given algorithm name.
    """
    normalized = normalize_algorithm(algorithm)
    entry = PQC_MAPPING.get(normalized)

    if not entry:
        # Fallback for unknown algorithms
        is_safe = "PQC" in normalized or "SAFE" in normalized
        return {
            "algorithm": algorithm,
            "normalized": normalized,
            "mapped": False,
            "kem": "ML-KEM-768" if not is_safe else None,
            "sig": "ML-DSA-65" if not is_safe else None,
            "alt_sig": None,
            "hash": None,
            "symmetric": None,
            "standard": PQCStandard.FIPS_203.value if not is_safe else PQCStandard.NONE.value,
            "complexity": MigrationComplexity.HIGH.value if not is_safe else MigrationComplexity.TRIVIAL.value,
            "effort_weeks": 4 if not is_safe else 0,
            "reason": "Unrecognized algorithm; manual cryptographic audit advised",
            "urgency": "MEDIUM" if not is_safe else "NONE",
            "quantum_safe": is_safe
        }

    return {
        "algorithm": algorithm,
        "normalized": normalized,
        "mapped": True,
        "kem": entry["kem"],
        "sig": entry["sig"],
        "alt_sig": entry.get("alt_sig"),
        "hash": entry["hash"],
        "symmetric": entry["symmetric"],
        "standard": entry["standard"],
        "complexity": entry["complexity"],
        "effort_weeks": entry["effort_weeks"],
        "reason": entry["reason"],
        "urgency": entry["urgency"],
        "quantum_safe": entry["quantum_safe"]
    }


# ============ 5. ENRICHMENT UTILITY ============
def enrich_findings(findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Enriches a list of finding dicts with a `.pqc` mapping block.
    """
    enriched: List[Dict[str, Any]] = []
    for f in findings:
        item = dict(f)
        algo = item.get("algorithm", "UNKNOWN")
        item["pqc"] = map_to_pqc(algo)
        enriched.append(item)
    return enriched


# ============ 6. MIGRATION SUMMARY ============
def get_migration_summary(findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregates findings into high-level migration metrics:
    total count, safe vs vulnerable, effort weeks, and distribution by standard and urgency.
    """
    total = len(findings)
    safe_count = 0
    vuln_count = 0
    total_effort = 0
    by_standard: Dict[str, int] = {}
    by_urgency: Dict[str, int] = {}

    for f in findings:
        pqc = f.get("pqc")
        if not pqc:
            pqc = map_to_pqc(f.get("algorithm", "UNKNOWN"))

        if pqc["quantum_safe"]:
            safe_count += 1
        else:
            vuln_count += 1

        total_effort += pqc.get("effort_weeks", 0)

        std = pqc.get("standard", PQCStandard.NONE.value)
        by_standard[std] = by_standard.get(std, 0) + 1

        urg = pqc.get("urgency", "NONE")
        by_urgency[urg] = by_urgency.get(urg, 0) + 1

    return {
        "total_findings": total,
        "quantum_safe": safe_count,
        "quantum_vulnerable": vuln_count,
        "total_effort_weeks": total_effort,
        "by_standard": by_standard,
        "by_urgency": by_urgency
    }
