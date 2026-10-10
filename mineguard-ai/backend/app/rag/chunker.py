"""
MineGuard AI — Document Chunker (Phase E2)
Intelligent recursive paragraph/sentence/word text chunker with sliding overlap.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import re
from app.rag.documents import Document


@dataclass
class Chunk:
    """Represents a text chunk for vector embedding and retrieval."""
    chunk_id: str
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class TextChunker:
    """
    Chunks textual documents with semantic awareness:
    1. Paragraph boundaries (double newline)
    2. Sentence boundaries (. ! ? .\n)
    3. Word boundaries (when sentences exceed chunk size)
    4. Sliding window overlap between chunks
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Regex for common abbreviations to avoid false sentence splits
        self.abbr_pattern = re.compile(
            r'\b(e\.g\.|i\.e\.|etc\.|fig\.|dr\.|mr\.|mrs\.|ms\.|vs\.|al\.|no\.|vol\.|sec\.|rev\.)\s*$',
            re.IGNORECASE
        )

    def _split_into_sentences(self, paragraph: str) -> List[str]:
        """Split paragraph into sentences while preserving standard abbreviations."""
        raw_tokens = re.split(r'(\. |\! |\? |\.\n)', paragraph)
        sentences = []
        current = ""

        i = 0
        while i < len(raw_tokens):
            part = raw_tokens[i]
            current += part
            # Check if this part is followed by a punctuation delimiter
            if i + 1 < len(raw_tokens):
                delim = raw_tokens[i + 1]
                # If current ends with abbreviation, don't split yet
                if self.abbr_pattern.search(current):
                    current += delim
                else:
                    current += delim
                    sentences.append(current.strip())
                    current = ""
                i += 2
            else:
                i += 1

        if current.strip():
            sentences.append(current.strip())

        return [s for s in sentences if s]

    def _split_long_sentence(self, sentence: str) -> List[str]:
        """Split a sentence exceeding chunk size on word boundaries."""
        words = sentence.split()
        segments = []
        current_words = []
        current_len = 0

        for word in words:
            word_len = len(word) + 1
            if current_len + word_len > self.chunk_size and current_words:
                segments.append(" ".join(current_words))
                # Keep small overlap of words if possible
                overlap_words = current_words[-3:] if len(current_words) > 3 else []
                current_words = overlap_words + [word]
                current_len = sum(len(w) + 1 for w in current_words)
            else:
                current_words.append(word)
                current_len += word_len

        if current_words:
            segments.append(" ".join(current_words))

        return segments

    def chunk_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Chunk]:
        """Chunk raw text and attach source metadata."""
        if metadata is None:
            metadata = {}

        source_id = metadata.get("source_id", "doc")
        raw_paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        # Collect normalized text segments (sentences or small paragraphs)
        segments: List[str] = []
        for para in raw_paragraphs:
            if len(para) <= self.chunk_size:
                segments.append(para)
            else:
                sentences = self._split_into_sentences(para)
                for sentence in sentences:
                    if len(sentence) <= self.chunk_size:
                        segments.append(sentence)
                    else:
                        sub_segments = self._split_long_sentence(sentence)
                        segments.extend(sub_segments)

        # Assemble chunks with chunk_size and chunk_overlap
        chunks: List[Chunk] = []
        current_chunk_parts: List[str] = []
        current_len = 0
        chunk_idx = 1

        for seg in segments:
            seg_len = len(seg)
            if current_len + seg_len + 1 > self.chunk_size and current_chunk_parts:
                chunk_text = "\n".join(current_chunk_parts)
                chunk_id = f"{source_id}-chunk-{chunk_idx:03d}"
                chunk_meta = dict(metadata)
                chunk_meta["chunk_index"] = chunk_idx
                chunk_meta["character_count"] = len(chunk_text)
                chunks.append(Chunk(chunk_id=chunk_id, text=chunk_text, metadata=chunk_meta))
                chunk_idx += 1

                # Overlap logic: carry over trailing content up to chunk_overlap characters
                overlap_parts = []
                overlap_len = 0
                for part in reversed(current_chunk_parts):
                    if overlap_len + len(part) <= self.chunk_overlap or not overlap_parts:
                        overlap_parts.insert(0, part)
                        overlap_len += len(part)
                    else:
                        break
                current_chunk_parts = overlap_parts + [seg]
                current_len = sum(len(p) + 1 for p in current_chunk_parts)
            else:
                current_chunk_parts.append(seg)
                current_len += seg_len + 1

        if current_chunk_parts:
            chunk_text = "\n".join(current_chunk_parts)
            chunk_id = f"{source_id}-chunk-{chunk_idx:03d}"
            chunk_meta = dict(metadata)
            chunk_meta["chunk_index"] = chunk_idx
            chunk_meta["character_count"] = len(chunk_text)
            chunks.append(Chunk(chunk_id=chunk_id, text=chunk_text, metadata=chunk_meta))

        return chunks

    def chunk_document(self, document: Document) -> List[Chunk]:
        """Chunk a full Document instance."""
        meta = {
            "source_id": document.id,
            "source_title": document.title,
            "source_url": document.url,
            "category": document.category,
            "year": document.year,
            "license": document.license
        }
        return self.chunk_text(document.full_text, metadata=meta)

    @staticmethod
    def get_statistics(chunks: List[Chunk]) -> Dict[str, Any]:
        """Compute summary statistics for a set of chunks."""
        total_chunks = len(chunks)
        if total_chunks == 0:
            return {"total_chunks": 0, "avg_chunk_size": 0, "by_document": {}}

        total_chars = sum(len(c.text) for c in chunks)
        avg_chunk_size = round(total_chars / total_chunks, 1)

        by_doc: Dict[str, int] = {}
        for c in chunks:
            doc_id = c.metadata.get("source_id", "unknown")
            by_doc[doc_id] = by_doc.get(doc_id, 0) + 1

        return {
            "total_chunks": total_chunks,
            "avg_chunk_size": avg_chunk_size,
            "by_document": by_doc
        }
