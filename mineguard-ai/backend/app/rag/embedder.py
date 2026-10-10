"""
MineGuard AI — Embedding Generation (Phase E3)
Sentence-Transformers embedding engine with graceful TF-IDF/n-gram hashing fallback.
"""

from typing import List, Optional, Dict, Any
import numpy as np
import hashlib
from pathlib import Path
from loguru import logger

# Supported model choices
MODEL_CHOICES: Dict[str, Dict[str, Any]] = {
    "all-MiniLM-L6-v2": {"dim": 384, "desc": "Default, fast, high semantic accuracy (384d)"},
    "all-mpnet-base-v2": {"dim": 768, "desc": "High accuracy sentence transformer (768d)"},
    "paraphrase-multilingual-MiniLM-L12-v2": {"dim": 384, "desc": "Multilingual model (384d)"},
    "hash-fallback-256": {"dim": 256, "desc": "Deterministic n-gram hash fallback (256d)"}
}


class HashFallbackEmbedder:
    """
    FALLBACK — Deterministic n-gram hash embedding engine.
    Used when sentence-transformers or PyTorch is not installed in the environment.
    Generates L2-normalized 256-dimensional vectors using word and character n-grams.
    """

    def __init__(self, dimension: int = 256):
        self.dimension = dimension
        logger.warning(
            f"FALLBACK EMBEDDER ACTIVE: Using deterministic {dimension}d hash embedder. "
            "Install sentence-transformers for production neural embeddings."
        )

    def _hash_token(self, token: str) -> int:
        h = hashlib.sha256(token.encode("utf-8")).digest()
        return int.from_bytes(h[:4], "little") % self.dimension

    def _embed_single(self, text: str) -> np.ndarray:
        vec = np.zeros(self.dimension, dtype=np.float32)
        words = text.lower().split()
        
        # Word unigrams
        for w in words:
            idx = self._hash_token(w)
            vec[idx] += 1.0

        # Word bigrams
        for i in range(len(words) - 1):
            bigram = f"{words[i]}_{words[i+1]}"
            idx = self._hash_token(bigram)
            vec[idx] += 1.5

        # Character trigrams for morphological and acronym matches (e.g. 'fips', 'pqc', 'rsa')
        clean = re_clean = "".join(c for c in text.lower() if c.isalnum() or c.isspace())
        for i in range(len(clean) - 2):
            trigram = clean[i:i+3]
            idx = self._hash_token(trigram)
            vec[idx] += 0.5

        # L2 normalization
        norm = np.linalg.norm(vec)
        if norm > 1e-12:
            vec /= norm
        return vec

    def embed(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, self.dimension), dtype=np.float32)
        vectors = [self._embed_single(t) for t in texts]
        return np.vstack(vectors).astype(np.float32)

    def embed_query(self, text: str) -> np.ndarray:
        return self._embed_single(text)


class Embedder:
    """
    Unified embedder interface. Uses sentence-transformers if available,
    falling back seamlessly to HashFallbackEmbedder if uninstalled.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", cache_dir: Optional[str] = None):
        self.model_name = model_name
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self._st_model = None
        self._fallback_embedder = None
        self.is_fallback = False

        if model_name in MODEL_CHOICES:
            self.dimension = MODEL_CHOICES[model_name]["dim"]
        else:
            self.dimension = 384

        self._init_backend()

    def _init_backend(self):
        """Attempt to load sentence_transformers, fallback cleanly if absent."""
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
            logger.info(f"Loading neural embedding model '{self.model_name}'...")
            self._st_model = SentenceTransformer(self.model_name)
            self.dimension = self._st_model.get_sentence_embedding_dimension()
            self.is_fallback = False
            logger.info(f"Loaded sentence-transformers model with dimension {self.dimension}.")
        except Exception as e:
            logger.warning(f"sentence-transformers unavailable ({e}). Initializing fallback hash embedder.")
            self.dimension = 256
            self.model_name = "hash-fallback-256"
            self._fallback_embedder = HashFallbackEmbedder(dimension=256)
            self.is_fallback = True

    def embed(self, texts: List[str]) -> np.ndarray:
        """Embed a list of strings into a 2D numpy array (n, dim)."""
        if not texts:
            return np.empty((0, self.dimension), dtype=np.float32)

        if not self.is_fallback and self._st_model is not None:
            embeddings = self._st_model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
            return embeddings.astype(np.float32)
        else:
            return self._fallback_embedder.embed(texts)

    def embed_query(self, text: str) -> np.ndarray:
        """Embed a single query string into a 1D vector of shape (dim,)."""
        arr = self.embed([text])
        return arr[0]

    def save_cache(self, embeddings: np.ndarray, file_path: str):
        """Cache embeddings array to disk as .npy."""
        p = Path(file_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        np.save(str(p), embeddings)
        logger.debug(f"Saved {embeddings.shape} embeddings cache to {file_path}")

    def load_cache(self, file_path: str) -> Optional[np.ndarray]:
        """Load cached embeddings from disk if file exists."""
        p = Path(file_path)
        if p.exists():
            arr = np.load(str(p))
            logger.debug(f"Loaded {arr.shape} embeddings cache from {file_path}")
            return arr
        return None
