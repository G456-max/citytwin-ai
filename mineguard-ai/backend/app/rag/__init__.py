"""
MineGuard AI — RAG & LLM Package (Phase E)
Retrieval-Augmented Generation, vector store, prompts, citations, and guardrails.
"""

from app.rag.documents import (
    Document,
    DOCUMENTS_METADATA,
    BUNDLED_EXCERPTS,
    download_documents
)
from app.rag.chunker import (
    TextChunker,
    Chunk
)
from app.rag.embedder import (
    Embedder,
    HashFallbackEmbedder,
    MODEL_CHOICES
)
from app.rag.vectorstore import (
    VectorStore,
    RetrievedChunk
)
from app.rag.retriever import (
    Retriever,
    ensure_index,
    rebuild_index,
    get_global_retriever
)
from app.rag.prompts import (
    build_prompt,
    SYSTEM_PROMPT,
    EXPLAIN_FINDING_PROMPT,
    EXPLAIN_CASCADE_PROMPT,
    COMPARE_ALGORITHMS_PROMPT,
    FREE_QUERY_PROMPT
)
from app.rag.llm_client import (
    LLMClient,
    RateLimiter
)
from app.rag.citations import (
    CitationExtractor,
    Citation
)
from app.rag.guardrails import (
    GuardrailPipeline,
    ALLOWED_ALGORITHMS,
    ALLOWED_STANDARDS
)

__all__ = [
    "Document",
    "DOCUMENTS_METADATA",
    "BUNDLED_EXCERPTS",
    "download_documents",
    "TextChunker",
    "Chunk",
    "Embedder",
    "HashFallbackEmbedder",
    "MODEL_CHOICES",
    "VectorStore",
    "RetrievedChunk",
    "Retriever",
    "ensure_index",
    "rebuild_index",
    "get_global_retriever",
    "build_prompt",
    "SYSTEM_PROMPT",
    "EXPLAIN_FINDING_PROMPT",
    "EXPLAIN_CASCADE_PROMPT",
    "COMPARE_ALGORITHMS_PROMPT",
    "FREE_QUERY_PROMPT",
    "LLMClient",
    "RateLimiter",
    "CitationExtractor",
    "Citation",
    "GuardrailPipeline",
    "ALLOWED_ALGORITHMS",
    "ALLOWED_STANDARDS",
]
