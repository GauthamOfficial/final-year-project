"""
Document → token-aware chunks (PRD §9.1.2).

Strategy:
- Chunk size: 512 tokens (PRD §9.1.2 spec)
- Overlap:    64 tokens (PRD §9.1.2 spec)
- Paragraph-aware: never split mid-sentence; coalesce paragraphs until the
  size budget is reached, then start a new chunk preserving overlap.

Token counting is intentionally simple — Gemini does not ship a public
tokenizer, and the embedding model accepts up to ~2k tokens, so a
whitespace-based heuristic with a 1.3× safety multiplier is sufficient for
chunking decisions (see PRD §9.5 for the budget envelope).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Iterator

DEFAULT_CHUNK_TOKENS = 512
DEFAULT_OVERLAP_TOKENS = 64
TOKEN_SAFETY_MULTIPLIER = 1.3

_PARAGRAPH_SPLIT = re.compile(r"\n{2,}|\r\n{2,}")
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")


@dataclass(frozen=True)
class Chunk:
    text: str
    token_estimate: int
    paragraph_index: int


def estimate_tokens(text: str) -> int:
    """Whitespace-based token estimate scaled for sub-word tokenisation."""
    if not text:
        return 0
    words = len(text.split())
    return max(1, int(words * TOKEN_SAFETY_MULTIPLIER))


def _iter_paragraphs(text: str) -> Iterator[str]:
    for paragraph in _PARAGRAPH_SPLIT.split(text):
        cleaned = paragraph.strip()
        if cleaned:
            yield cleaned


def _iter_sentences(paragraph: str) -> Iterator[str]:
    for sent in _SENTENCE_SPLIT.split(paragraph):
        cleaned = sent.strip()
        if cleaned:
            yield cleaned


def chunk_text(
    text: str,
    chunk_tokens: int = DEFAULT_CHUNK_TOKENS,
    overlap_tokens: int = DEFAULT_OVERLAP_TOKENS,
) -> list[Chunk]:
    """Split a document into ~`chunk_tokens` chunks with `overlap_tokens` overlap."""

    if not text or not text.strip():
        return []

    chunks: list[Chunk] = []
    buffer: list[str] = []
    buffer_tokens = 0

    def flush(index: int) -> None:
        nonlocal buffer, buffer_tokens
        if not buffer:
            return
        merged = " ".join(buffer).strip()
        chunks.append(
            Chunk(
                text=merged,
                token_estimate=estimate_tokens(merged),
                paragraph_index=index,
            )
        )
        if overlap_tokens > 0:
            tail: list[str] = []
            tail_tokens = 0
            for sent in reversed(buffer):
                tail.insert(0, sent)
                tail_tokens += estimate_tokens(sent)
                if tail_tokens >= overlap_tokens:
                    break
            buffer = tail
            buffer_tokens = tail_tokens
        else:
            buffer = []
            buffer_tokens = 0

    for p_idx, paragraph in enumerate(_iter_paragraphs(text)):
        for sentence in _iter_sentences(paragraph):
            sent_tokens = estimate_tokens(sentence)
            if buffer_tokens + sent_tokens > chunk_tokens and buffer:
                flush(p_idx)
            buffer.append(sentence)
            buffer_tokens += sent_tokens
        # Paragraph boundary nudges the chunker to flush early if we're close.
        if buffer_tokens >= chunk_tokens * 0.9:
            flush(p_idx)

    flush(-1)
    return chunks


def batched(iterable: Iterable, size: int) -> Iterator[list]:
    batch: list = []
    for item in iterable:
        batch.append(item)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch
