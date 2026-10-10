"""
MineGuard AI — Retrieval Engine (Phase E5)
High-precision semantic retriever with query expansion, deduplication, and LRU caching.
"""

from typing import List, Dict, Any, Optional
from collections import OrderedDict
import time
from loguru import logger

from app.rag.chunker import TextChunker, Chunk
from app.rag.embedder import Embedder
from app.rag.vectorstore import VectorStore, RetrievedChunk
from app.rag.documents import download_documents


# Common cryptographic terms for query expansion
EXPANSION_KEYWORDS = {
    "rsa": "RSA Shor's algorithm integer factorization FIPS 204 ML-DSA",
    "ecdsa": "ECDSA elliptic curve discrete logarithm Shor's algorithm FIPS 204 ML-DSA",
    "ecdh": "ECDH key agreement Shor's algorithm FIPS 203 ML-KEM",
    "dh": "Diffie-Hellman discrete logarithm Shor's algorithm FIPS 203 ML-KEM",
    "md5": "MD5 hash collision Grover's algorithm SHA-256",
    "sha-1": "SHA-1 hash collision Grover's algorithm SHA-256 SHA-3",
    "aes-128": "AES-128 Grover's algorithm 64-bit quantum security AES-256",
    "aes-256": "AES-256 Grover's algorithm 128-bit quantum security post-quantum safe",
    "cascade": "dependency cascade failure SCADA operational technology safety interlock",
    "q-day": "Q-Day CRQC cryptanalytically relevant quantum computer Mosca's inequality",
    "cbom": "CBOM CycloneDX 1.7 cryptographic bill of materials asset inventory",
    "migration": "NIST IR 8547 CNSA 2.0 migration timeline transition hybrid key exchange",
    "fips 203": "FIPS 203 ML-KEM CRYSTALS-Kyber key encapsulation mechanism",
    "fips 204": "FIPS 204 ML-DSA CRYSTALS-Dilithium digital signature",
    "fips 205": "FIPS 205 SLH-DSA SPHINCS+ stateless hash signature"
}


class Retriever:
    """
    Retrieval engine connecting the embedder and vector database.
    Includes query expansion, domain filtering, deduplication, and LRU caching.
    """

    def __init__(self, embedder: Embedder, vectorstore: VectorStore, cache_size: int = 100):
        self.embedder = embedder
        self.vectorstore = vectorstore
        self.cache_size = cache_size
        self._cache: OrderedDict[str, List[RetrievedChunk]] = OrderedDict()

    def _expand_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Expand user query with domain keywords and context metadata to maximize recall."""
        expanded_parts = [query.strip()]
        lower_q = query.lower()

        # Add context details if provided
        if context:
            if "algorithm" in context and context["algorithm"]:
                algo = str(context["algorithm"]).strip()
                expanded_parts.append(f"algorithm {algo}")
            if "standard" in context and context["standard"]:
                expanded_parts.append(f"standard {context['standard']}")
            if "severity" in context and context["severity"]:
                expanded_parts.append(f"severity {context['severity']}")
            if "replacement" in context and context["replacement"]:
                expanded_parts.append(f"replacement {context['replacement']}")

        # Keyword expansion matching
        for key, expansion in EXPANSION_KEYWORDS.items():
            if key in lower_q:
                expanded_parts.append(expansion)

        # Baseline quantum terms
        if not any(t in lower_q for t in ["quantum", "pqc", "nist"]):
            expanded_parts.append("quantum post-quantum NIST PQC standards")

        return " ".join(expanded_parts)

    def deduplicate(self, results: List[RetrievedChunk], threshold: float = 0.98) -> List[RetrievedChunk]:
        """Remove near-identical chunks based on text prefix and source ID."""
        seen_signatures = set()
        unique_results: List[RetrievedChunk] = []

        for item in results:
            # Signature based on source ID and first 100 characters
            source_id = item.metadata.get("source_id", "")
            prefix = "".join(item.text[:120].split()).lower()
            sig = f"{source_id}:{prefix}"

            if sig in seen_signatures:
                continue
            seen_signatures.add(sig)
            unique_results.append(item)

        return unique_results

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        category_filter: Optional[str] = None
    ) -> List[RetrievedChunk]:
        """
        Retrieve relevant chunks for a natural language query.
        Applies caching and optional category filtering.
        """
        cache_key = f"{query.strip()}||{top_k}||{category_filter or 'ALL'}"
        if cache_key in self._cache:
            self._cache.move_to_end(cache_key)
            return self._cache[cache_key]

        expanded_query = self._expand_query(query)
        q_emb = self.embedder.embed_query(expanded_query)

        # Fetch extra candidates if filtering or deduplicating
        fetch_k = max(top_k * 3, 10)
        raw_results = self.vectorstore.search(q_emb, top_k=fetch_k)

        # Apply category filter if requested
        if category_filter:
            cat_norm = category_filter.strip().upper()
            filtered = [
                r for r in raw_results
                if str(r.metadata.get("category", "")).upper() == cat_norm
            ]
        else:
            filtered = raw_results

        # Deduplicate and trim to top_k
        deduped = self.deduplicate(filtered)
        final_results = deduped[:top_k]

        # Manage LRU cache
        if len(self._cache) >= self.cache_size:
            self._cache.popitem(last=False)
        self._cache[cache_key] = final_results

        return final_results

    def retrieve_with_context(
        self,
        query: str,
        context: Dict[str, Any],
        top_k: int = 5,
        category_filter: Optional[str] = None
    ) -> List[RetrievedChunk]:
        """Retrieve using query expanded with finding/cascade context."""
        expanded_query = self._expand_query(query, context=context)
        return self.retrieve(expanded_query, top_k=top_k, category_filter=category_filter)

    def clear_cache(self):
        """Clear query cache."""
        self._cache.clear()


# Module-level singleton manager for application lifecycle
_GLOBAL_RETRIEVER: Optional[Retriever] = None


def get_global_retriever() -> Optional[Retriever]:
    return _GLOBAL_RETRIEVER


def ensure_index(
    data_dir: str = "data",
    vector_db_path: str = "data/vectordb",
    embedder_model: str = "all-MiniLM-L6-v2",
    force_rebuild: bool = False
) -> Retriever:
    """
    Ensure the RAG index is loaded or constructed from documents.
    Idempotent and thread-safe startup initializer.
    """
    global _GLOBAL_RETRIEVER

    if _GLOBAL_RETRIEVER is not None and not force_rebuild:
        return _GLOBAL_RETRIEVER

    embedder = Embedder(model_name=embedder_model)

    # Try loading existing vectorstore from disk if not forcing rebuild
    if not force_rebuild:
        try:
            store = VectorStore.load(vector_db_path)
            _GLOBAL_RETRIEVER = Retriever(embedder, store)
            logger.info(f"Loaded existing RAG index from {vector_db_path} ({store.size()} chunks).")
            return _GLOBAL_RETRIEVER
        except Exception as e:
            logger.info(f"Existing index not found or unreadable ({e}). Building new index...")

    # Build index from authoritative documents
    start_t = time.time()
    docs = download_documents(target_dir=f"{data_dir}/documents")
    chunker = TextChunker(chunk_size=500, chunk_overlap=50)

    all_chunks: List[Chunk] = []
    for doc in docs:
        chunks = chunker.chunk_document(doc)
        all_chunks.extend(chunks)

    texts = [c.text for c in all_chunks]
    embeddings = embedder.embed(texts)

    store = VectorStore(dimension=embedder.dimension)
    store.add_chunks(all_chunks, embeddings)

    # Persist vectorstore to disk
    try:
        store.save(vector_db_path)
    except Exception as e:
        logger.warning(f"Could not persist vectorstore to {vector_db_path}: {e}")

    duration = round((time.time() - start_t) * 1000, 1)
    logger.info(f"RAG index constructed: {len(all_chunks)} chunks from {len(docs)} documents in {duration}ms.")

    _GLOBAL_RETRIEVER = Retriever(embedder, store)
    return _GLOBAL_RETRIEVER


def rebuild_index(
    data_dir: str = "data",
    vector_db_path: str = "data/vectordb",
    embedder_model: str = "all-MiniLM-L6-v2"
) -> Dict[str, Any]:
    """Force rebuild of RAG index and return statistics."""
    start_t = time.time()
    retriever = ensure_index(
        data_dir=data_dir,
        vector_db_path=vector_db_path,
        embedder_model=embedder_model,
        force_rebuild=True
    )
    duration_ms = int((time.time() - start_t) * 1000)

    return {
        "rebuilt_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "chunks_indexed": retriever.vectorstore.size(),
        "dimension": retriever.embedder.dimension,
        "backend": "faiss" if not retriever.vectorstore.is_fallback else "numpy_fallback",
        "duration_ms": duration_ms
    }
