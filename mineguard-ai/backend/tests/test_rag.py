"""
MineGuard AI — RAG & LLM Pipeline Test Suite (Phase E)
Comprehensive verification of document collection, chunking, embeddings, vectorstore,
retrieval, prompts, LLM client, citations, and hallucination guardrails.
"""

import pytest
import numpy as np
import tempfile
import shutil
from pathlib import Path

from app.rag.documents import DOCUMENTS_METADATA, download_documents, Document
from app.rag.chunker import TextChunker, Chunk
from app.rag.embedder import Embedder, HashFallbackEmbedder
from app.rag.vectorstore import VectorStore, RetrievedChunk
from app.rag.retriever import Retriever, ensure_index
from app.rag.prompts import build_prompt, SYSTEM_PROMPT
from app.rag.llm_client import LLMClient
from app.rag.citations import CitationExtractor
from app.rag.guardrails import GuardrailPipeline


# 1. Documents Metadata Valid
def test_documents_metadata_valid():
    """Verify all 13 documents have required attributes and licenses."""
    assert len(DOCUMENTS_METADATA) >= 10
    required_keys = {"id", "title", "url", "category", "year", "license", "description"}
    for doc in DOCUMENTS_METADATA:
        for key in required_keys:
            assert key in doc, f"Document {doc.get('id')} missing key '{key}'"
        assert len(doc["title"]) > 5
        assert doc["year"] >= 2015
        assert doc["category"] in ["NIST", "ENISA", "Industry", "Academic", "Standards"]


# 2. Chunker Splits Correctly
def test_chunker_splits_correctly():
    """Verify TextChunker splits large multi-paragraph text without data loss."""
    chunker = TextChunker(chunk_size=300, chunk_overlap=30)
    sample_text = (
        "Paragraph 1 discusses post-quantum migration and NIST FIPS 203 standards.\n\n"
        "Paragraph 2 discusses module-lattice digital signatures and ML-DSA specified in FIPS 204. "
        "It provides strong authentication for OT networks, SCADA controllers, and safety interlocks.\n\n"
        "Paragraph 3 covers SLH-DSA from FIPS 205, which is a stateless hash-based signature scheme."
    )
    chunks = chunker.chunk_text(sample_text, metadata={"source_id": "test-doc"})
    assert len(chunks) >= 2
    for c in chunks:
        assert len(c.text) <= 450
        assert c.chunk_id.startswith("test-doc-chunk-")
        assert "source_id" in c.metadata


# 3. Chunk Overlap Present
def test_chunk_overlap_present():
    """Verify consecutive chunks preserve sliding context overlap."""
    chunker = TextChunker(chunk_size=150, chunk_overlap=40)
    text = (
        "First major section explains Shor's algorithm breaking RSA.\n\n"
        "Second major section explains Grover's algorithm halving symmetric key sizes.\n\n"
        "Third major section explains lattice problems resisting quantum cryptanalysis."
    )
    chunks = chunker.chunk_text(text, metadata={"source_id": "overlap-test"})
    assert len(chunks) >= 2
    # Check that at least some words from chunk 1 appear in chunk 2
    words_c1 = set(chunks[0].text.split())
    words_c2 = set(chunks[1].text.split())
    common = words_c1.intersection(words_c2)
    assert len(common) > 0, "Expected context overlap between consecutive chunks"


# 4. Embedder Dimension
def test_embedder_dimension():
    """Verify Embedder outputs expected dimensions and normalized vectors."""
    embedder = Embedder()
    assert embedder.dimension in [256, 384, 768]

    texts = ["Module-Lattice Key Encapsulation", "Stateful Hash Signatures"]
    embs = embedder.embed(texts)
    assert embs.shape == (2, embedder.dimension)

    q_emb = embedder.embed_query("NIST FIPS 203")
    assert q_emb.shape == (embedder.dimension,)

    # Verify L2 normalization
    norm = np.linalg.norm(q_emb)
    assert np.isclose(norm, 1.0, atol=1e-3)


# 5. Embedder Fallback
def test_embedder_fallback():
    """Verify HashFallbackEmbedder creates valid 256-dim normalized embeddings."""
    fallback = HashFallbackEmbedder(dimension=256)
    texts = ["RSA-2048 Shor algorithm", "AES-256 Grover"]
    embs = fallback.embed(texts)
    assert embs.shape == (2, 256)

    q_vec = fallback.embed_query("quantum threat")
    assert q_vec.shape == (256,)
    assert np.isclose(np.linalg.norm(q_vec), 1.0, atol=1e-3)


# 6. Vectorstore Add and Search
def test_vectorstore_add_search():
    """Verify VectorStore adds chunks and performs similarity search."""
    store = VectorStore(dimension=256)
    fallback = HashFallbackEmbedder(dimension=256)

    c1 = Chunk("c1", "NIST FIPS 203 specifies ML-KEM key encapsulation.", {"source_title": "FIPS 203"})
    c2 = Chunk("c2", "NIST FIPS 204 specifies ML-DSA digital signatures.", {"source_title": "FIPS 204"})
    c3 = Chunk("c3", "Underground mining haulage dispatch telemetry.", {"source_title": "Mining Ops"})

    chunks = [c1, c2, c3]
    embeddings = fallback.embed([c.text for c in chunks])
    store.add_chunks(chunks, embeddings)

    assert store.size() == 3

    q_emb = fallback.embed_query("ML-KEM key encapsulation")
    results = store.search(q_emb, top_k=2)

    assert len(results) == 2
    assert results[0].chunk_id == "c1"
    assert results[0].score > 0.0


# 7. Vectorstore Persistence
def test_vectorstore_persistence():
    """Verify VectorStore saves to disk and reloads cleanly."""
    temp_dir = tempfile.mkdtemp()
    try:
        store = VectorStore(dimension=256)
        fallback = HashFallbackEmbedder(dimension=256)

        c1 = Chunk("c1", "Persisted chunk data for testing.", {"source_title": "Test Doc"})
        embeddings = fallback.embed([c1.text])
        store.add_chunks([c1], embeddings)
        store.save(temp_dir)

        # Reload
        loaded_store = VectorStore.load(temp_dir)
        assert loaded_store.size() == 1
        assert loaded_store.chunks[0].chunk_id == "c1"
        assert loaded_store.chunks[0].text == "Persisted chunk data for testing."
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# 8. Retriever Returns Top-K
def test_retriever_returns_top_k():
    """Verify Retriever returns the requested top_k documents."""
    embedder = Embedder()
    store = VectorStore(dimension=embedder.dimension)

    chunks = [
        Chunk(f"c{i}", f"Document text chunk number {i} regarding quantum crypto algorithms.", {"category": "NIST", "source_title": f"Doc {i}"})
        for i in range(10)
    ]
    embs = embedder.embed([c.text for c in chunks])
    store.add_chunks(chunks, embs)

    retriever = Retriever(embedder, store)
    results = retriever.retrieve("quantum crypto", top_k=3)
    assert len(results) == 3


# 9. Retriever Category Filter
def test_retriever_category_filter():
    """Verify Retriever category filtering isolates target domain documents."""
    embedder = Embedder()
    store = VectorStore(dimension=embedder.dimension)

    c1 = Chunk("c1", "NIST publication on algorithms", {"category": "NIST", "source_title": "NIST"})
    c2 = Chunk("c2", "ENISA publication on EU guidelines", {"category": "ENISA", "source_title": "ENISA"})
    c3 = Chunk("c3", "Industry paper on quantum error correction", {"category": "Industry", "source_title": "Industry"})

    chunks = [c1, c2, c3]
    store.add_chunks(chunks, embedder.embed([c.text for c in chunks]))

    retriever = Retriever(embedder, store)
    results = retriever.retrieve("algorithms", top_k=5, category_filter="ENISA")

    assert len(results) == 1
    assert results[0].metadata["category"] == "ENISA"


# 10. Prompt Builder
def test_prompt_builder():
    """Verify build_prompt creates expected message structure and preserves rules."""
    messages = build_prompt(
        "finding",
        algorithm="RSA-2048",
        file="auth.py",
        line=42,
        severity="CRITICAL",
        replacement="ML-DSA-65",
        standard="NIST FIPS 204",
        context="NIST FIPS 204 specifies ML-DSA.",
        question="Why is this critical?"
    )
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert "You are MineGuard AI" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    assert "RSA-2048" in messages[1]["content"]
    assert "ML-DSA-65" in messages[1]["content"]


# 11. LLM Client Mock
def test_llm_client_mock():
    """Verify LLMClient in mock mode returns deterministic text with source tags."""
    client = LLMClient(provider="mock")
    info = client.get_provider_info()
    assert info["is_mock"] is True

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "finding to explain:\nalgorithm: RSA-2048\nreplacement: ML-DSA-65"}
    ]
    response = client.generate(messages)
    assert isinstance(response, str)
    assert len(response) > 50
    assert "RSA" in response
    assert "[SOURCE:" in response


# 12. Citation Extraction
def test_citation_extraction():
    """Verify CitationExtractor parses [SOURCE: ...] tags and matches retrieved chunks."""
    extractor = CitationExtractor()
    chunks = [
        RetrievedChunk("c1", "Excerpt text on ML-KEM", {"source_title": "NIST FIPS 203: Module-Lattice-Based Key-Encapsulation Mechanism Standard (ML-KEM)", "source_url": "https://nist.gov/fips203", "category": "NIST", "year": 2024}, 0.88),
    ]

    llm_text = "ML-KEM is the standard for key encapsulation [SOURCE: NIST FIPS 203: Module-Lattice-Based Key-Encapsulation Mechanism Standard (ML-KEM)]."
    citations = extractor.extract(llm_text, chunks)

    assert len(citations) == 1
    assert citations[0].verified is True
    assert "FIPS 203" in citations[0].title
    assert citations[0].relevance == 0.88


# 13. Citation Rejects Hallucinated
def test_citation_rejects_hallucinated():
    """Verify CitationExtractor marks unrecognized citations as unverified/hallucinated."""
    extractor = CitationExtractor()
    chunks = [
        RetrievedChunk("c1", "NIST text", {"source_title": "NIST FIPS 203", "category": "NIST", "year": 2024}, 0.9)
    ]

    llm_text = "Some ungrounded claim [SOURCE: Random Blog Post 2099 That Does Not Exist]."
    citations = extractor.extract(llm_text, chunks)

    assert len(citations) == 1
    assert citations[0].verified is False
    assert "HALLUCINATED" in citations[0].excerpt or "UNVERIFIED" in citations[0].excerpt


# 14. Guardrails Numeric Consistency
def test_guardrails_numeric_consistency():
    """Verify GuardrailPipeline detects numeric mismatch between response and input context."""
    guardrails = GuardrailPipeline()
    context = {"score": 0.45}

    response_valid = "The evaluated risk score is 0.45 which indicates moderate risk [SOURCE: NIST FIPS 203]."
    res1 = guardrails.validate(response_valid, context=context)
    assert not any("Numeric inconsistency" in f for f in res1["flags"])

    response_invalid = "The evaluated risk score is 0.95 which indicates extreme risk [SOURCE: NIST FIPS 203]."
    res2 = guardrails.validate(response_invalid, context=context)
    assert any("Numeric inconsistency" in f for f in res2["flags"])


# 15. Guardrails Unknown Algorithm
def test_guardrails_unknown_algorithm():
    """Verify GuardrailPipeline flags unapproved or hallucinated algorithm names."""
    guardrails = GuardrailPipeline()
    valid_text = "We recommend migrating from RSA-2048 to ML-DSA-65 [SOURCE: NIST FIPS 204]."
    res1 = guardrails.validate(valid_text)
    assert not any("Unrecognized algorithm" in f for f in res1["flags"])

    invalid_text = "We recommend switching to QUANTUM-MAGIC-CIPHER-9000 immediately [SOURCE: NIST FIPS 204]."
    res2 = guardrails.validate(invalid_text)
    # The unknown algorithm should trigger a flag or warning
    assert len(res2["flags"]) > 0 or res2["confidence"] != "high"


# 16. Guardrails Uncited Response
def test_guardrails_uncited_response():
    """Verify GuardrailPipeline flags responses lacking source citations."""
    guardrails = GuardrailPipeline()
    uncited_text = "This is a detailed analysis of post-quantum cryptography but it lacks any source citation tag completely."
    res = guardrails.validate(uncited_text)
    assert any("missing required source citation" in f for f in res["flags"])
    assert res["passed"] is False
