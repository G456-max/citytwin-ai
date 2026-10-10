"""
MineGuard AI — Vector Database (Phase E4)
FAISS-powered vector store with brute-force NumPy cosine similarity fallback.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import json
from pathlib import Path
import numpy as np
from datetime import datetime
from loguru import logger

from app.rag.chunker import Chunk


@dataclass
class RetrievedChunk:
    """Retrieved search result chunk with cosine similarity score."""
    chunk_id: str
    text: str
    metadata: Dict[str, Any]
    score: float


class VectorStore:
    """
    Vector store supporting FAISS IndexFlatIP (cosine similarity)
    with seamless in-memory NumPy matrix search fallback when FAISS is unavailable.
    """

    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.chunks: List[Chunk] = []
        self.embeddings: Optional[np.ndarray] = None
        self._faiss_index = None
        self.is_fallback = False

        self._init_backend()

    def _init_backend(self):
        """Attempt to instantiate FAISS IndexFlatIP; fallback to numpy if absent."""
        try:
            import faiss  # type: ignore
            self._faiss_index = faiss.IndexFlatIP(self.dimension)
            self.is_fallback = False
            logger.info(f"Initialized FAISS IndexFlatIP with dimension {self.dimension}.")
        except Exception as e:
            logger.info(f"FAISS unavailable ({e}). Using NumPy matrix cosine similarity fallback.")
            self.is_fallback = True

    def _normalize(self, v: np.ndarray) -> np.ndarray:
        """L2-normalize vectors for cosine similarity via inner product."""
        if v.ndim == 1:
            norm = np.linalg.norm(v)
            return (v / norm).astype(np.float32) if norm > 1e-12 else v.astype(np.float32)
        norms = np.linalg.norm(v, axis=1, keepdims=True)
        norms[norms < 1e-12] = 1.0
        return (v / norms).astype(np.float32)

    def add_chunks(self, chunks: List[Chunk], embeddings: np.ndarray):
        """Add chunks and corresponding embeddings into the store."""
        if len(chunks) == 0:
            return

        if embeddings.shape[0] != len(chunks):
            raise ValueError(f"Mismatch: {len(chunks)} chunks vs {embeddings.shape[0]} embeddings")

        norm_embeddings = self._normalize(embeddings)

        # Update FAISS index if present
        if not self.is_fallback and self._faiss_index is not None:
            self._faiss_index.add(norm_embeddings)

        # Update in-memory storage
        self.chunks.extend(chunks)
        if self.embeddings is None:
            self.embeddings = norm_embeddings
        else:
            self.embeddings = np.vstack([self.embeddings, norm_embeddings])

        logger.debug(f"Added {len(chunks)} chunks to VectorStore (total: {len(self.chunks)}).")

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[RetrievedChunk]:
        """Search top-k most similar chunks using cosine similarity."""
        if len(self.chunks) == 0 or self.embeddings is None:
            return []

        q_norm = self._normalize(query_embedding).reshape(1, -1)

        if not self.is_fallback and self._faiss_index is not None:
            scores, indices = self._faiss_index.search(q_norm, min(top_k, len(self.chunks)))
            top_scores = scores[0]
            top_indices = indices[0]
        else:
            # NumPy inner product between normalized query and normalized embeddings
            sims = np.dot(self.embeddings, q_norm.T).flatten()
            k = min(top_k, len(self.chunks))
            top_indices = np.argsort(sims)[::-1][:k]
            top_scores = sims[top_indices]

        results: List[RetrievedChunk] = []
        for idx, score in zip(top_indices, top_scores):
            if idx < 0 or idx >= len(self.chunks):
                continue
            chunk = self.chunks[idx]
            # Clip cosine similarity to [0.0, 1.0]
            clamped_score = float(np.clip(score, 0.0, 1.0))
            results.append(
                RetrievedChunk(
                    chunk_id=chunk.chunk_id,
                    text=chunk.text,
                    metadata=dict(chunk.metadata),
                    score=round(clamped_score, 4)
                )
            )

        return results

    def size(self) -> int:
        """Return the number of indexed chunks."""
        return len(self.chunks)

    def save(self, path: str):
        """
        Persist vector store to disk:
        - index.faiss (or embeddings.npy)
        - chunks.json
        - meta.json
        """
        p = Path(path)
        p.mkdir(parents=True, exist_ok=True)

        # 1. Save chunks metadata & text
        chunks_data = [
            {"chunk_id": c.chunk_id, "text": c.text, "metadata": c.metadata}
            for c in self.chunks
        ]
        with open(p / "chunks.json", "w", encoding="utf-8") as f:
            json.dump(chunks_data, f, indent=2)

        # 2. Save embeddings/index
        if not self.is_fallback and self._faiss_index is not None:
            try:
                import faiss
                faiss.write_index(self._faiss_index, str(p / "index.faiss"))
            except Exception as e:
                logger.warning(f"Failed to write FAISS index file: {e}")

        # Always save embeddings as numpy for fallback loading
        if self.embeddings is not None:
            np.save(str(p / "embeddings.npy"), self.embeddings)

        # 3. Save build info metadata
        meta = {
            "dimension": self.dimension,
            "total_chunks": len(self.chunks),
            "backend": "faiss" if not self.is_fallback else "numpy_fallback",
            "saved_at": datetime.utcnow().isoformat()
        }
        with open(p / "meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        logger.info(f"Saved VectorStore ({len(self.chunks)} chunks, dim={self.dimension}) to {path}")

    @classmethod
    def load(cls, path: str) -> "VectorStore":
        """Load an existing VectorStore from disk."""
        p = Path(path)
        if not (p / "chunks.json").exists() or not (p / "meta.json").exists():
            raise FileNotFoundError(f"VectorStore directory incomplete at {path}")

        with open(p / "meta.json", "r", encoding="utf-8") as f:
            meta = json.load(f)

        dimension = meta.get("dimension", 384)
        store = cls(dimension=dimension)

        # Load chunks
        with open(p / "chunks.json", "r", encoding="utf-8") as f:
            chunks_data = json.load(f)

        store.chunks = [
            Chunk(chunk_id=item["chunk_id"], text=item["text"], metadata=item.get("metadata", {}))
            for item in chunks_data
        ]

        # Load FAISS index or NumPy embeddings
        faiss_file = p / "index.faiss"
        npy_file = p / "embeddings.npy"

        if faiss_file.exists() and not store.is_fallback:
            try:
                import faiss
                store._faiss_index = faiss.read_index(str(faiss_file))
                logger.debug(f"Loaded FAISS index from {faiss_file}")
            except Exception as e:
                logger.warning(f"Could not load FAISS index ({e}), falling back to numpy")
                store.is_fallback = True

        if npy_file.exists():
            store.embeddings = np.load(str(npy_file))
            if store.is_fallback and store._faiss_index is None:
                logger.debug(f"Loaded NumPy embeddings from {npy_file}")

        logger.info(f"Loaded VectorStore from {path} with {len(store.chunks)} chunks.")
        return store
