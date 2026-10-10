"""
MineGuard AI — Hallucination Guardrails (Phase E9)
Six-point deterministic validation pipeline enforcing numeric fidelity, algorithm whitelisting,
citation presence, and standard compliance.
"""

from typing import List, Dict, Any, Optional, Set
import re
from loguru import logger


# Whitelist of recognized cryptographic algorithms
ALLOWED_ALGORITHMS: Set[str] = {
    "RSA", "RSA-2048", "RSA-3072", "RSA-4096",
    "ECDSA", "ECDSA-256", "ECDSA-384",
    "ECDH", "DH", "DIFFIE-HELLMAN",
    "DSA", "MD5", "SHA-1", "SHA-256", "SHA-384", "SHA-512", "SHA-3",
    "AES", "AES-128", "AES-192", "AES-256",
    "ML-KEM", "ML-KEM-512", "ML-KEM-768", "ML-KEM-1024",
    "ML-DSA", "ML-DSA-44", "ML-DSA-65", "ML-DSA-87",
    "SLH-DSA", "SLH-DSA-128", "SLH-DSA-256",
    "XMSS", "LMS", "HSS", "FALCON", "KYBER", "DILITHIUM", "SPHINCS+"
}

# Whitelist of recognized standards and publications
ALLOWED_STANDARDS: Set[str] = {
    "FIPS 203", "FIPS 204", "FIPS 205",
    "NIST IR 8547", "CNSA 2.0",
    "SP 800-208", "SP 800-57",
    "RFC 8391", "RFC 8554",
    "CYCLONEDX 1.7", "ENISA", "MOSCA"
}


class GuardrailPipeline:
    """
    Validates LLM-generated explanations against strict deterministic rules:
    1. Numeric consistency against context inputs
    2. Cryptographic algorithm whitelist
    3. Standards and specifications whitelist
    4. Citation presence
    5. Uncertainty acknowledgment
    6. Length sanity constraints
    """

    def __init__(self):
        self.min_length = 50
        self.max_length = 2000

    def check_numeric_consistency(
        self,
        response_text: str,
        expected_context: Dict[str, Any]
    ) -> List[str]:
        """
        Extract float scores and integer counts from response and verify against context.
        Flags cases where the LLM invents or hallucinates differing numeric scores.
        """
        flags = []
        
        # Check specifically for score mentions like "score 0.XX" or "risk score of 0.XX"
        score_matches = re.findall(r'\b(?:score|risk)\s*(?:of|is|:)?\s*([0-9]+\.[0-9]+)\b', response_text, re.IGNORECASE)
        
        if "score" in expected_context and expected_context["score"] is not None:
            expected_score = float(expected_context["score"])
            for match in score_matches:
                found_score = float(match)
                if abs(found_score - expected_score) > 0.05:
                    flags.append(
                        f"Numeric inconsistency: Response claims score {found_score}, but context has {expected_score}"
                    )

        if "risk_score" in expected_context and expected_context["risk_score"] is not None:
            expected_score = float(expected_context["risk_score"])
            for match in score_matches:
                found_score = float(match)
                if abs(found_score - expected_score) > 0.05:
                    flags.append(
                        f"Numeric inconsistency: Response claims risk score {found_score}, but context has {expected_score}"
                    )

        return flags

    def check_algorithms(self, response_text: str) -> List[str]:
        """
        Identify crypto algorithm tokens mentioned in text and verify against whitelist.
        """
        flags = []
        # Find potential uppercase algorithmic acronyms and compound names up to 30 chars
        potential_algos = re.findall(r'\b[A-Z][A-Z0-9\-]{2,30}\b', response_text)
        
        # Filter out common English acronyms, HTTP words, etc.
        ignored_tokens = {
            "NIST", "FIPS", "PQC", "CRQC", "HNDL", "OT", "IT", "SCADA", "PLC", "VPN",
            "TLS", "SSL", "CA", "PKI", "IIOT", "CPU", "RAM", "MTU", "HTTP", "JSON",
            "XML", "SOURCE", "API", "DOE", "NSA", "ISO", "IEC", "IETF", "RFC", "USA", "EU"
        }

        # 1. Check contextual phrases (e.g. "switching to XYZ", "algorithm XYZ")
        context_triggers = re.findall(r'\b(?:algorithm|cipher|cryptosystem|primitive|migrating to|switching to|use|using)\s+([A-Za-z0-9\-_]+)', response_text, re.IGNORECASE)
        for token in context_triggers:
            upper_token = token.upper()
            if upper_token not in ignored_tokens and upper_token not in ALLOWED_ALGORITHMS:
                if not any(allowed in upper_token for allowed in ALLOWED_ALGORITHMS):
                    flags.append(f"Unrecognized algorithm referenced: '{token}'")

        # 2. Check tokens that look like crypto algorithms or ciphers
        for token in potential_algos:
            upper_token = token.upper()
            if upper_token in ignored_tokens:
                continue

            looks_like_algo = any(prefix in upper_token for prefix in ["RSA", "ECD", "DSA", "AES", "SHA", "MD", "KEM", "SLH", "LMS", "XMS", "CIPHER"])
            if looks_like_algo and upper_token not in ALLOWED_ALGORITHMS:
                if not any(allowed in upper_token for allowed in ALLOWED_ALGORITHMS):
                    flags.append(f"Unrecognized algorithm referenced: '{token}'")

        # Deduplicate flags
        return list(dict.fromkeys(flags))

    def check_standards(self, response_text: str) -> List[str]:
        """
        Verify that referenced standards follow authorized designations.
        """
        flags = []
        # Find patterns like "FIPS XXX" or "SP 800-XXX" or "RFC XXXX"
        std_patterns = re.findall(r'\b(FIPS\s+\d+|SP\s+800\-\d+|RFC\s+\d+|CNSA\s+[\d\.]+)\b', response_text, re.IGNORECASE)
        for std in std_patterns:
            std_upper = std.upper().strip()
            # Standardize spacing
            std_norm = re.sub(r'\s+', ' ', std_upper)
            if not any(allowed in std_norm for allowed in ALLOWED_STANDARDS):
                flags.append(f"Unrecognized cryptographic standard referenced: '{std}'")

        return flags

    def check_citations(self, response_text: str) -> List[str]:
        """Verify presence of at least one [SOURCE: ...] tag."""
        if "[SOURCE:" not in response_text:
            return ["Response is missing required source citation tag [SOURCE: ...]"]
        return []

    def check_uncertainty(self, response_text: str) -> bool:
        """Return True if the response acknowledges lack of context/information."""
        lower = response_text.lower()
        phrases = [
            "don't have enough information",
            "do not have enough information",
            "not enough information in my sources",
            "insufficient information"
        ]
        return any(p in lower for p in phrases)

    def validate(
        self,
        response_text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute full guardrail validation pipeline.
        Returns:
            passed: bool
            flags: List[str]
            confidence: "high" | "medium" | "low"
            reason: str
            sanitized_text: str
        """
        if context is None:
            context = {}

        flags: List[str] = []
        sanitized_text = response_text

        # 1. Length check
        if len(sanitized_text) < self.min_length:
            flags.append(f"Response too brief ({len(sanitized_text)} chars < {self.min_length} chars)")
        elif len(sanitized_text) > self.max_length:
            sanitized_text = sanitized_text[:self.max_length] + " [TRUNCATED]"
            flags.append(f"Response exceeded max length ({len(response_text)} chars); truncated to {self.max_length}")

        # 2. Uncertainty check
        is_uncertain = self.check_uncertainty(sanitized_text)

        # 3. Numeric consistency check
        num_flags = self.check_numeric_consistency(sanitized_text, context)
        flags.extend(num_flags)

        # 4. Algorithm whitelist check
        algo_flags = self.check_algorithms(sanitized_text)
        flags.extend(algo_flags)

        # 5. Standards check
        std_flags = self.check_standards(sanitized_text)
        flags.extend(std_flags)

        # 6. Citation presence check
        if not is_uncertain:
            cite_flags = self.check_citations(sanitized_text)
            flags.extend(cite_flags)

        # Determine overall pass status and confidence level
        passed = (len(flags) == 0)

        if len(flags) == 0:
            confidence = "high"
            reason = "Passed all 6 guardrail checks (numeric, algorithmic, standards, citations, length, uncertainty)."
        elif len(flags) == 1 and ("missing required source citation" in flags[0] or "too brief" in flags[0]):
            confidence = "medium"
            reason = f"Minor guardrail warning: {flags[0]}"
        else:
            confidence = "low"
            reason = f"Guardrail flags triggered: {'; '.join(flags)}"

        return {
            "passed": passed,
            "flags": flags,
            "confidence": confidence,
            "reason": reason,
            "sanitized_text": sanitized_text
        }
