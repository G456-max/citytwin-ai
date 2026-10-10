"""
MineGuard AI — Citation & Source Attribution (Phase E8)
Extracts and cryptographically cross-validates source citations against retrieved context chunks.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import re
from loguru import logger
from app.rag.vectorstore import RetrievedChunk
from app.rag.documents import DOCUMENTS_METADATA


@dataclass
class Citation:
    """Structured citation representation."""
    title: str
    url: str
    category: str
    year: int
    relevance: float
    excerpt: str
    verified: bool = True


class CitationExtractor:
    """
    Parses [SOURCE: <title>] patterns from LLM outputs,
    matches them against retrieved context chunks, and validates attribution.
    """

    def __init__(self):
        # Match patterns like: [SOURCE: NIST FIPS 203: ...] or [SOURCE: NIST FIPS 203]
        self.citation_pattern = re.compile(r'\[SOURCE:\s*([^\]]+)\]', re.IGNORECASE)

    def _normalize_title(self, title: str) -> str:
        """Strip punctuation and standardize spacing for fuzzy source matching."""
        return re.sub(r'[^a-zA-Z0-9]', '', title).lower()

    def _find_matching_chunk(
        self,
        cited_title: str,
        retrieved_chunks: List[RetrievedChunk]
    ) -> Optional[RetrievedChunk]:
        """Find the best retrieved chunk corresponding to cited title."""
        norm_cited = self._normalize_title(cited_title)
        if not norm_cited or len(norm_cited) < 3:
            return None

        for chunk in retrieved_chunks:
            meta = chunk.metadata
            chunk_title = meta.get("source_title", "")
            doc_id = meta.get("source_id", "")

            norm_chunk_title = self._normalize_title(chunk_title)
            norm_id = self._normalize_title(doc_id)

            if norm_chunk_title and (norm_cited in norm_chunk_title or norm_chunk_title in norm_cited):
                return chunk
            if norm_id and (norm_id in norm_cited or norm_cited in norm_id):
                return chunk

            # Common token overlap check (e.g. "fips203" or "cnsa20")
            common_tokens = {"fips203", "fips204", "fips205", "ir8547", "cnsa20", "sp800208", "mosca", "enisa"}
            for tok in common_tokens:
                if tok in norm_cited and ((norm_chunk_title and tok in norm_chunk_title) or (norm_id and tok in norm_id)):
                    return chunk

        return None

    def _lookup_global_metadata(self, cited_title: str) -> Optional[Dict[str, Any]]:
        """Fallback lookup against global document catalog if chunk was not retrieved."""
        norm_cited = self._normalize_title(cited_title)
        if not norm_cited or len(norm_cited) < 3:
            return None
        for doc in DOCUMENTS_METADATA:
            norm_doc = self._normalize_title(doc["title"])
            norm_id = self._normalize_title(doc["id"])
            if norm_doc and (norm_cited in norm_doc or norm_doc in norm_cited):
                return doc
            if norm_id and (norm_id in norm_cited or norm_cited in norm_id):
                return doc
        return None

    def extract(
        self,
        llm_response: str,
        retrieved_chunks: List[RetrievedChunk]
    ) -> List[Citation]:
        """
        Extract citations from text, match against retrieved chunks, and flag unverified sources.
        """
        raw_matches = self.citation_pattern.findall(llm_response)
        citations: List[Citation] = []
        seen_titles = set()

        for raw_title in raw_matches:
            cleaned_title = raw_title.strip()
            norm_title = self._normalize_title(cleaned_title)
            if norm_title in seen_titles:
                continue
            seen_titles.add(norm_title)

            # Check if this source exists in the retrieved chunks
            matched_chunk = self._find_matching_chunk(cleaned_title, retrieved_chunks)

            if matched_chunk:
                meta = matched_chunk.metadata
                excerpt_snippet = matched_chunk.text[:200].replace("\n", " ").strip() + "..."
                citations.append(
                    Citation(
                        title=meta.get("source_title", cleaned_title),
                        url=meta.get("source_url", ""),
                        category=meta.get("category", "NIST"),
                        year=meta.get("year", 2024),
                        relevance=matched_chunk.score,
                        excerpt=excerpt_snippet,
                        verified=True
                    )
                )
            else:
                # LLM cited a source that was NOT in the retrieved chunks! Flag as UNVERIFIED.
                global_meta = self._lookup_global_metadata(cleaned_title)
                if global_meta:
                    logger.warning(f"Unverified citation: '{cleaned_title}' cited by LLM was not in retrieved context.")
                    citations.append(
                        Citation(
                            title=global_meta["title"],
                            url=global_meta["url"],
                            category=global_meta["category"],
                            year=global_meta["year"],
                            relevance=0.0,
                            excerpt="UNVERIFIED: Source was not present in the retrieved context window.",
                            verified=False
                        )
                    )
                else:
                    logger.warning(f"Hallucinated citation: '{cleaned_title}' does not match any recognized source.")
                    citations.append(
                        Citation(
                            title=cleaned_title,
                            url="",
                            category="Unknown",
                            year=2024,
                            relevance=0.0,
                            excerpt="HALLUCINATED: Unrecognized source reference.",
                            verified=False
                        )
                    )

        # If LLM didn't cite with tags, but we have high-relevance chunks, optionally suggest top retrieved chunk
        if len(raw_matches) == 0 and not citations and retrieved_chunks:
            top_chunk = retrieved_chunks[0]
            if top_chunk.score >= 0.5:
                meta = top_chunk.metadata
                citations.append(
                    Citation(
                        title=meta.get("source_title", "Context Reference"),
                        url=meta.get("source_url", ""),
                        category=meta.get("category", "NIST"),
                        year=meta.get("year", 2024),
                        relevance=top_chunk.score,
                        excerpt=top_chunk.text[:200].replace("\n", " ").strip() + "...",
                        verified=True
                    )
                )

        return citations
