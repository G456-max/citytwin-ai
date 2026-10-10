"""
MineGuard AI — Explain API Routes (Phase E10)
RAG and LLM explanation endpoints with retrieval augmentation, citation extraction,
and hallucination guardrail verification.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
import time
from loguru import logger

from app.config import settings
from app.models.schemas import (
    ExplainFindingRequest,
    ExplainCascadeRequest,
    ExplainCompareRequest,
    ExplainFreeRequest,
    ExplainFullResponse,
    CitationModel,
    GuardrailResultModel,
    ExplainRequest,
    ExplainResponse
)
from app.rag.documents import DOCUMENTS_METADATA, download_documents
from app.rag.retriever import ensure_index, rebuild_index, get_global_retriever
from app.rag.prompts import build_prompt
from app.rag.llm_client import LLMClient
from app.rag.citations import CitationExtractor
from app.rag.guardrails import GuardrailPipeline


router = APIRouter(prefix="/explain", tags=["explain"])

# Shared pipeline instances
_llm_client = LLMClient()
_citation_extractor = CitationExtractor()
_guardrails = GuardrailPipeline()


def _get_active_retriever():
    """Ensure active retriever instance is ready."""
    retriever = get_global_retriever()
    if retriever is None:
        retriever = ensure_index(
            data_dir="data",
            vector_db_path=settings.VECTOR_DB_PATH,
            embedder_model=settings.EMBEDDER_MODEL
        )
    return retriever


def _execute_rag_pipeline(
    template_name: str,
    query_for_retrieval: str,
    context_dict: Dict[str, Any],
    top_k: int = 5
) -> ExplainFullResponse:
    """Core orchestrator executing Retrieval -> Prompt -> LLM -> Citation -> Guardrails."""
    start_time = time.time()
    retriever = _get_active_retriever()

    # 1. Retrieve top-k chunks with context expansion
    chunks = retriever.retrieve_with_context(
        query=query_for_retrieval,
        context=context_dict,
        top_k=top_k
    )

    context_text = "\n\n".join([f"[{c.metadata.get('source_title', 'Source')}]:\n{c.text}" for c in chunks])
    if not context_text.strip():
        context_text = "No additional context documents available."

    prompt_kwargs = {**context_dict, "context": context_text}

    # 2. Build prompt messages
    messages = build_prompt(template_name, **prompt_kwargs)

    # 3. LLM generation
    llm_output = _llm_client.generate(messages, temperature=0.2, max_tokens=500)

    # 4. Extract citations and match against retrieved chunks
    citations_data = _citation_extractor.extract(llm_output, chunks)
    citations_models = [
        CitationModel(
            title=c.title,
            url=c.url,
            category=c.category,
            year=c.year,
            relevance=c.relevance,
            excerpt=c.excerpt,
            verified=c.verified
        )
        for c in citations_data
    ]

    # 5. Hallucination guardrail evaluation
    guardrail_res = _guardrails.validate(llm_output, context=context_dict)

    duration_ms = int((time.time() - start_time) * 1000)
    provider_info = _llm_client.get_provider_info()

    return ExplainFullResponse(
        answer=guardrail_res["sanitized_text"],
        sources=citations_models,
        guardrails=GuardrailResultModel(
            passed=guardrail_res["passed"],
            flags=guardrail_res["flags"],
            confidence=guardrail_res["confidence"],
            reason=guardrail_res["reason"]
        ),
        model=provider_info["model"],
        duration_ms=duration_ms
    )


# =========================================================================
# ENDPOINTS
# =========================================================================

@router.post("/finding", response_model=ExplainFullResponse)
async def explain_finding(payload: ExplainFindingRequest):
    """
    Explain a specific cryptographic finding (algorithm, severity, file, replacement)
    grounded in NIST FIPS 203/204/205 standards.
    """
    finding = payload.finding
    ctx = {
        "algorithm": finding.algorithm,
        "file": finding.file,
        "line": finding.line,
        "severity": finding.severity,
        "replacement": finding.replacement or "ML-KEM-768 or ML-DSA-65",
        "standard": finding.standard or "NIST FIPS 203 / FIPS 204",
        "score": finding.score,
        "risk_score": finding.risk_score,
        "question": payload.question
    }
    query = f"Explain post-quantum risk of {finding.algorithm} and migration to {ctx['replacement']}"
    return _execute_rag_pipeline("finding", query, ctx, top_k=settings.RAG_TOP_K)


@router.post("/cascade", response_model=ExplainFullResponse)
async def explain_cascade(payload: ExplainCascadeRequest):
    """
    Explain why a cascade failure occurs across mining OT systems
    and its operational safety implications under a given Q-Day horizon.
    """
    ctx = {
        "q_day": payload.q_day,
        "total_down": payload.total_down,
        "total_systems": payload.total_systems,
        "critical_down": payload.critical_down,
        "safety_impact": payload.safety_impact,
        "question": payload.question
    }
    query = f"Mining infrastructure cascade failure quantum threat horizon {payload.q_day} safety impact"
    return _execute_rag_pipeline("cascade", query, ctx, top_k=settings.RAG_TOP_K)


@router.post("/compare", response_model=ExplainFullResponse)
async def explain_compare(payload: ExplainCompareRequest):
    """
    Compare a legacy classical algorithm against a recommended PQC replacement
    citing relevant NIST standards.
    """
    ctx = {
        "current_algorithm": payload.current_algorithm,
        "recommended_algorithm": payload.recommended_algorithm,
        "standard": payload.standard or "NIST PQC Standards",
        "question": payload.question
    }
    query = f"Compare {payload.current_algorithm} with {payload.recommended_algorithm} post-quantum security"
    return _execute_rag_pipeline("compare", query, ctx, top_k=settings.RAG_TOP_K)


@router.post("/free", response_model=ExplainFullResponse)
async def explain_free(payload: ExplainFreeRequest):
    """
    Free-form natural language cybersecurity query grounded in indexed PQC literature.
    """
    ctx = payload.context or {}
    ctx["question"] = payload.question
    return _execute_rag_pipeline("free", payload.question, ctx, top_k=settings.RAG_TOP_K)


@router.post("", response_model=ExplainResponse)
async def explain_generic(payload: ExplainRequest):
    """
    General explanation endpoint ensuring backward compatibility with test stubs.
    """
    ctx = payload.context or {}
    ctx["question"] = payload.question
    full_resp = _execute_rag_pipeline("free", payload.question, ctx, top_k=settings.RAG_TOP_K)
    
    # Map sources to titles/strings for backward compatibility
    source_titles = [s.title for s in full_resp.sources]
    return ExplainResponse(
        answer=full_resp.answer,
        sources=source_titles,
        confidence=full_resp.guardrails.confidence
    )


@router.get("/sources", response_model=List[Dict[str, Any]])
async def get_indexed_sources():
    """
    Return catalog of all available post-quantum authoritative sources and metadata.
    """
    return DOCUMENTS_METADATA


@router.get("/stats")
async def get_rag_stats():
    """
    Return operational statistics on RAG vector store, chunk counts, model, and caching.
    """
    retriever = _get_active_retriever()
    provider_info = _llm_client.get_provider_info()

    return {
        "total_chunks": retriever.vectorstore.size(),
        "total_documents": len(DOCUMENTS_METADATA),
        "embedder_model": retriever.embedder.model_name,
        "embedding_dimension": retriever.embedder.dimension,
        "vector_backend": "faiss" if not retriever.vectorstore.is_fallback else "numpy_cosine_matrix",
        "llm_provider": provider_info["provider"],
        "llm_model": provider_info["model"],
        "cached_queries": len(retriever._cache),
        "rate_limit_per_min": provider_info["rate_limit_per_min"]
    }


@router.post("/rebuild-index")
async def trigger_rebuild_index():
    """
    Force re-indexing of all authoritative documents into the vector store.
    """
    result = rebuild_index(
        data_dir="data",
        vector_db_path=settings.VECTOR_DB_PATH,
        embedder_model=settings.EMBEDDER_MODEL
    )
    return result
