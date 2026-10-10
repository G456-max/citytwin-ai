"""
MineGuard AI — Prompt Templates (Phase E6)
Strict system guidelines, citation directives, and structured scenario prompts.
"""

from typing import List, Dict, Any


SYSTEM_PROMPT = """You are MineGuard AI, a cybersecurity assistant for mining infrastructure. You help security teams understand post-quantum cryptography risks and migration planning.

RULES:
1. Answer ONLY using the provided context documents.
2. Always cite sources using [SOURCE: <title>].
3. If the context does not contain the answer, say "I don't have enough information in my sources to answer this."
4. NEVER invent numbers, dates, or algorithm names.
5. NEVER change calculated scores — you explain, not compute.
6. Use plain, professional language.
7. When discussing risk, always mention the specific NIST standard (FIPS 203, FIPS 204, or FIPS 205).
"""

EXPLAIN_FINDING_PROMPT = """Context documents:
{context}

Finding to explain:
- Algorithm: {algorithm}
- File: {file}
- Line: {line}
- Severity: {severity}
- Replacement: {replacement}
- Standard: {standard}

Question: {question}

Answer in 3-5 sentences. Cite at least one source using [SOURCE: <title>].
"""

EXPLAIN_CASCADE_PROMPT = """Context documents:
{context}

Cascade scenario:
- Q-Day: {q_day}
- Systems down: {total_down}/{total_systems}
- Critical systems affected: {critical_down}
- Safety impact: {safety_impact}

Question: {question}

Explain why this cascade occurs and what it means for mining safety.
Answer in 3-5 sentences. Cite sources using [SOURCE: <title>].
"""

COMPARE_ALGORITHMS_PROMPT = """Context documents:
{context}

Compare these algorithms for mining infrastructure:
- Current: {current_algorithm}
- Recommended: {recommended_algorithm}
- NIST Standard: {standard}

Question: Why is the recommended algorithm safer?

Explain in 3-5 sentences with citations using [SOURCE: <title>].
"""

FREE_QUERY_PROMPT = """Context documents:
{context}

Question: {question}

Answer using the context above in 3-5 sentences. Cite at least one source using [SOURCE: <title>].
"""


TEMPLATES = {
    "finding": EXPLAIN_FINDING_PROMPT,
    "cascade": EXPLAIN_CASCADE_PROMPT,
    "compare": COMPARE_ALGORITHMS_PROMPT,
    "free": FREE_QUERY_PROMPT,
}


def build_prompt(template_name: str, **kwargs) -> List[Dict[str, str]]:
    """
    Build a standard chat completion message list for the LLM:
    [
      {"role": "system", "content": SYSTEM_PROMPT},
      {"role": "user", "content": filled_template}
    ]
    """
    if template_name not in TEMPLATES:
        raise ValueError(f"Unknown prompt template '{template_name}'. Available: {list(TEMPLATES.keys())}")

    template_str = TEMPLATES[template_name]

    # Normalize defaults for common fields if omitted
    defaults = {
        "context": "No additional context documents provided.",
        "algorithm": "Unknown",
        "file": "unknown_file",
        "line": 0,
        "severity": "MEDIUM",
        "replacement": "ML-KEM-768 or ML-DSA-65",
        "standard": "NIST FIPS 203 / FIPS 204",
        "question": "Explain the post-quantum risk and migration path.",
        "q_day": "2029-2030",
        "total_down": 0,
        "total_systems": 20,
        "critical_down": 0,
        "safety_impact": "Operational disruption",
        "current_algorithm": "RSA-2048",
        "recommended_algorithm": "ML-DSA-65"
    }

    fill_dict = {**defaults, **kwargs}
    user_content = template_str.format(**fill_dict)

    return [
        {"role": "system", "content": SYSTEM_PROMPT.strip()},
        {"role": "user", "content": user_content.strip()}
    ]
