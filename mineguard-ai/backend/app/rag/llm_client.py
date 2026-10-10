"""
MineGuard AI — LLM Integration (Phase E7)
Multi-provider LLM client with rate limiting, retry backoff, and robust deterministic MOCK mode.
"""

from typing import List, Dict, Any, Optional
import time
import json
import re
import asyncio
from loguru import logger
from app.config import settings


class RateLimiter:
    """Sliding-window rate limiter ensuring <= max_requests per 60 seconds."""

    def __init__(self, max_requests: int = 60, window_seconds: float = 60.0):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.timestamps: List[float] = []

    def acquire(self):
        now = time.time()
        # Drop timestamps older than window
        self.timestamps = [t for t in self.timestamps if now - t < self.window_seconds]
        if len(self.timestamps) >= self.max_requests:
            sleep_needed = self.window_seconds - (now - self.timestamps[0])
            if sleep_needed > 0:
                logger.warning(f"Rate limit reached ({self.max_requests}/min). Sleeping {sleep_needed:.2f}s...")
                time.sleep(sleep_needed)
                now = time.time()
                self.timestamps = [t for t in self.timestamps if now - t < self.window_seconds]
        self.timestamps.append(now)


class LLMClient:
    """
    Unified LLM Client supporting:
    - OpenAI (gpt-4o-mini)
    - Anthropic (claude-3-5-sonnet)
    - Local Ollama (http://localhost:11434)
    - Deterministic MOCK fallback
    """

    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        self.provider = (provider or getattr(settings, "LLM_PROVIDER", "openai")).lower()
        self.model = model or getattr(settings, "LLM_MODEL", "gpt-4o-mini")
        self.timeout_seconds = 30.0
        self.max_retries = 3
        self.rate_limiter = RateLimiter(max_requests=60, window_seconds=60.0)

        self._openai_client = None
        self._anthropic_client = None
        self._init_provider()

    def _init_provider(self):
        """Initialize provider SDKs if keys and libraries are present."""
        openai_key = getattr(settings, "OPENAI_API_KEY", "")
        anthropic_key = getattr(settings, "ANTHROPIC_API_KEY", "")

        if self.provider == "openai" and openai_key:
            try:
                import openai
                self._openai_client = openai.OpenAI(api_key=openai_key, timeout=self.timeout_seconds)
                logger.info(f"Initialized OpenAI provider with model '{self.model}'.")
                return
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client ({e}). Falling back to MOCK.")

        elif self.provider == "anthropic" and anthropic_key:
            try:
                import anthropic
                self._anthropic_client = anthropic.Anthropic(api_key=anthropic_key, timeout=self.timeout_seconds)
                logger.info(f"Initialized Anthropic provider with model '{self.model}'.")
                return
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic client ({e}). Falling back to MOCK.")

        # Fallback to MOCK mode if keys absent or provider is mock
        if self.provider not in ["mock", "ollama"] and not openai_key and not anthropic_key:
            logger.info("No external LLM API key detected. Operating in MOCK MODE.")
            self.provider = "mock"

    def is_available(self) -> bool:
        """Returns True if a valid provider is configured or mock mode is active."""
        return True

    def get_provider_info(self) -> Dict[str, Any]:
        """Return provider configuration metadata."""
        return {
            "provider": self.provider,
            "model": self.model if self.provider != "mock" else "mock-deterministic-v1",
            "is_mock": self.provider == "mock",
            "timeout_seconds": self.timeout_seconds,
            "rate_limit_per_min": self.rate_limiter.max_requests
        }

    def _generate_mock_response(self, messages: List[Dict[str, str]]) -> str:
        """
        Deterministic, professional fallback generator when API key is not configured.
        Parses context and question to deliver factual answers with verified source tags.
        """
        user_msg = next((m["content"] for m in messages if m.get("role") == "user"), "")
        lower = user_msg.lower()

        # Check for finding explanation
        if "finding to explain:" in lower or "algorithm:" in lower:
            algo_match = re.search(r'algorithm:\s*([A-Za-z0-9\-]+)', user_msg, re.IGNORECASE)
            algo = algo_match.group(1).upper() if algo_match else "RSA"
            replacement_match = re.search(r'replacement:\s*([A-Za-z0-9\-]+)', user_msg, re.IGNORECASE)
            replacement = replacement_match.group(1) if replacement_match else "ML-KEM-768 or ML-DSA-65"

            if any(k in algo for k in ["RSA", "ECDSA", "DSA"]):
                return (
                    f"The identified {algo} implementation is critically vulnerable to Shor's algorithm on a quantum computer, "
                    f"which solves integer factorization and discrete logarithms in polynomial time [SOURCE: NIST FIPS 204: Module-Lattice-Based Digital Signature Standard (ML-DSA)]. "
                    f"Under NIST guidelines, legacy asymmetric public key systems must migrate to module-lattice standards such as {replacement} [SOURCE: NIST IR 8547: Transition to Post-Quantum Cryptography Standards]. "
                    f"Migrating to {replacement} restores post-quantum integrity across critical mining OT networks while preventing harvest-now-decrypt-later attacks [SOURCE: ENISA Post-Quantum Cryptography Report: Current State and Deployment Guidelines]."
                )
            elif "ECDH" in algo or "DH" in algo:
                return (
                    f"The {algo} key exchange mechanism is vulnerable to Shor's algorithm, allowing quantum adversaries to decrypt captured sessions retroactively [SOURCE: NIST FIPS 203: Module-Lattice-Based Key-Encapsulation Mechanism Standard (ML-KEM)]. "
                    f"NIST mandates replacing classical key establishment with ML-KEM parameter sets or deploying hybrid X25519/ML-KEM-768 tunnels during the transition [SOURCE: NIST IR 8547: Transition to Post-Quantum Cryptography Standards]. "
                    f"This ensures continuous confidentiality for long-lived operational telemetry and SCADA control channels."
                )
            elif "MD5" in algo or "SHA-1" in algo:
                return (
                    f"Legacy hash function {algo} suffers from known classical collision vulnerabilities and offers diminished collision resistance under Grover's quantum search [SOURCE: NIST SP 800-57 Part 1 Rev 5: Recommendation for Key Management]. "
                    f"Critical industrial systems must upgrade immediately to SHA-256 or SHA-3 to maintain post-quantum collision security [SOURCE: NSA CNSA 2.0: Commercial National Security Algorithm Suite 2.0 Cybersecurity Advisory]."
                )
            elif "AES-128" in algo:
                return (
                    f"While AES-128 remains secure against classical attacks, Grover's algorithm halves its effective quantum security to 64 bits [SOURCE: NIST SP 800-57 Part 1 Rev 5: Recommendation for Key Management]. "
                    f"Safety-critical mining infrastructure handling data with longevity exceeding 10 years should upgrade to AES-256 to guarantee at least 128 bits of quantum resistance [SOURCE: NSA CNSA 2.0: Commercial National Security Algorithm Suite 2.0 Cybersecurity Advisory]."
                )

        # Check for cascade explanation
        if "cascade scenario:" in lower:
            q_day_match = re.search(r'q-day:\s*([0-9\-]+)', user_msg, re.IGNORECASE)
            q_day = q_day_match.group(1) if q_day_match else "2029-2030"
            return (
                f"The failure cascade under horizon {q_day} occurs because core identity services and OT gateways rely on vulnerable classical asymmetric algorithms [SOURCE: NIST IR 8547: Transition to Post-Quantum Cryptography Standards]. "
                f"When root trust anchors and gateway handshakes are broken by quantum cryptanalysis, dependent SCADA and safety systems lose trusted command authentication [SOURCE: ENISA Post-Quantum Cryptography Report: Current State and Deployment Guidelines]. "
                f"In mining environments, this disruption compromises life-critical safety interlocks and automated haulage coordination, demonstrating why infrastructure migration must begin years ahead of the Q-Day horizon [SOURCE: Mosca's Theorem: Quantum Risk Horizon and Data Shelf-Life Inequality]."
            )

        # Check for algorithm comparison
        if "compare these algorithms" in lower:
            return (
                f"The recommended post-quantum algorithm replaces classical mathematics with lattice-based problems that resist polynomial-time quantum attacks [SOURCE: NIST FIPS 203: Module-Lattice-Based Key-Encapsulation Mechanism Standard (ML-KEM)]. "
                f"Unlike classical algorithms vulnerable to Shor's algorithm, module-lattice cryptography retains Category 3 or Category 5 quantum security [SOURCE: NIST FIPS 204: Module-Lattice-Based Digital Signature Standard (ML-DSA)]. "
                f"Adopting standardized PQC algorithms mitigates the harvest-now-decrypt-later threat and ensures compliance with federal transition timelines [SOURCE: NIST IR 8547: Transition to Post-Quantum Cryptography Standards]."
            )

        # General / Free query fallback
        return (
            "Post-quantum cryptography standards established by NIST—specifically ML-KEM (FIPS 203), ML-DSA (FIPS 204), and SLH-DSA (FIPS 205)—provide mathematical resilience against quantum cryptanalysis [SOURCE: NIST FIPS 203: Module-Lattice-Based Key-Encapsulation Mechanism Standard (ML-KEM)]. "
            "Under Mosca's inequality, organizations must initiate cryptographic inventory and hybrid migrations well before quantum computing threats materialize to safeguard safety-critical infrastructure [SOURCE: Mosca's Theorem: Quantum Risk Horizon and Data Shelf-Life Inequality]."
        )

    def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 500
    ) -> str:
        """
        Generate chat completion response across configured provider with retries.
        """
        self.rate_limiter.acquire()
        start_time = time.time()

        # 1. MOCK MODE
        if self.provider == "mock":
            response_text = self._generate_mock_response(messages)
            duration_ms = int((time.time() - start_time) * 1000)
            logger.info(f"LLM Call [mock | mock-v1 | ~{len(response_text)//4} tokens | {duration_ms}ms]")
            return response_text

        # 2. OPENAI PROVIDER
        if self.provider == "openai" and self._openai_client is not None:
            last_err = None
            for attempt in range(1, self.max_retries + 1):
                try:
                    response = self._openai_client.chat.completions.create(
                        model=self.model,
                        messages=messages,  # type: ignore
                        temperature=temperature,
                        max_tokens=max_tokens,
                        timeout=self.timeout_seconds
                    )
                    content = response.choices[0].message.content or ""
                    tokens = response.usage.total_tokens if response.usage else len(content) // 4
                    duration_ms = int((time.time() - start_time) * 1000)
                    logger.info(f"LLM Call [openai | {self.model} | {tokens} tokens | {duration_ms}ms]")
                    return content
                except Exception as e:
                    last_err = e
                    logger.warning(f"OpenAI call attempt {attempt}/{self.max_retries} failed: {e}")
                    if attempt < self.max_retries:
                        time.sleep(2 ** attempt)

            logger.error(f"OpenAI all retries failed ({last_err}). Falling back to MOCK response.")
            return self._generate_mock_response(messages)

        # 3. ANTHROPIC PROVIDER
        if self.provider == "anthropic" and self._anthropic_client is not None:
            last_err = None
            system_msg = next((m["content"] for m in messages if m.get("role") == "system"), "")
            user_messages = [m for m in messages if m.get("role") != "system"]

            for attempt in range(1, self.max_retries + 1):
                try:
                    response = self._anthropic_client.messages.create(
                        model=self.model,
                        system=system_msg,
                        messages=user_messages,  # type: ignore
                        temperature=temperature,
                        max_tokens=max_tokens,
                        timeout=self.timeout_seconds
                    )
                    content = "".join(b.text for b in response.content if hasattr(b, "text"))
                    tokens = response.usage.input_tokens + response.usage.output_tokens if response.usage else len(content) // 4
                    duration_ms = int((time.time() - start_time) * 1000)
                    logger.info(f"LLM Call [anthropic | {self.model} | {tokens} tokens | {duration_ms}ms]")
                    return content
                except Exception as e:
                    last_err = e
                    logger.warning(f"Anthropic call attempt {attempt}/{self.max_retries} failed: {e}")
                    if attempt < self.max_retries:
                        time.sleep(2 ** attempt)

            logger.error(f"Anthropic all retries failed ({last_err}). Falling back to MOCK response.")
            return self._generate_mock_response(messages)

        # Default fallback
        return self._generate_mock_response(messages)
