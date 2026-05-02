"""
Embedding clients used by the RAG pipeline (PRD §9.1.2 → §9.2).

The primary backend is Google Gemini (`models/text-embedding-004` per PRD).
A deterministic local fallback (`HashEmbeddingClient`) is shipped so:

  • Unit tests run without API access.
  • Prompt 3A's `ingest_knowledge_base` works offline against a local
    ChromaDB for development before keys are provisioned.

`get_embedding_client()` picks the backend based on `settings.GEMINI_API_KEY`.
"""

from __future__ import annotations

import hashlib
import logging
import math
import os
import struct
import time
from typing import Sequence

from django.conf import settings

logger = logging.getLogger("lankaguide.core.embeddings")

EMBEDDING_DIM = 768  # Matches Gemini text-embedding-004


class EmbeddingClient:
    name: str = "base"
    dimension: int = EMBEDDING_DIM

    def embed(self, text: str) -> list[float]:  # pragma: no cover - abstract
        raise NotImplementedError

    def embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]


class HashEmbeddingClient(EmbeddingClient):
    """
    Deterministic offline embedding (SHA-512-derived, 768-d, unit-norm).
    Useless for real semantic retrieval, but stable and zero-dependency,
    which is exactly what tests need.
    """

    name = "hash-deterministic"

    def embed(self, text: str) -> list[float]:
        seed = hashlib.sha512(text.encode("utf-8")).digest()
        floats: list[float] = []
        # 768 floats * 4 bytes = 3072 bytes; SHA-512 gives 64. Tile + xor.
        i = 0
        while len(floats) < self.dimension:
            chunk = hashlib.sha512(seed + i.to_bytes(2, "big")).digest()
            for offset in range(0, len(chunk), 4):
                if len(floats) >= self.dimension:
                    break
                (raw,) = struct.unpack("I", chunk[offset : offset + 4])
                # Map to [-1, 1)
                floats.append((raw / 0xFFFFFFFF) * 2 - 1)
            i += 1
        norm = math.sqrt(sum(x * x for x in floats)) or 1.0
        return [x / norm for x in floats]


class GeminiEmbeddingClient(EmbeddingClient):
    """Gemini-backed embedding (PRD §9.1.2). Uses exponential backoff (PRD §14.2)."""

    name = "gemini"

    def __init__(self, model: str | None = None, max_retries: int = 5):
        import google.generativeai as genai

        api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set; cannot use GeminiEmbeddingClient.")
        genai.configure(api_key=api_key)
        self._genai = genai
        self.model = model or settings.GEMINI_EMBEDDING_MODEL
        self.max_retries = max_retries

    def _embed_once(self, text: str) -> list[float]:
        result = self._genai.embed_content(
            model=self.model,
            content=text,
            task_type="retrieval_document",
        )
        embedding = result["embedding"] if isinstance(result, dict) else result.embedding
        return list(embedding)

    def embed(self, text: str) -> list[float]:
        delay = 1.0
        last_exc: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                return self._embed_once(text)
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                logger.warning(
                    "Gemini embed failed (attempt %s/%s): %s",
                    attempt + 1,
                    self.max_retries,
                    exc,
                )
                time.sleep(delay)
                delay = min(delay * 2, 30)
        raise RuntimeError(f"Gemini embed failed after {self.max_retries} retries") from last_exc


def get_embedding_client() -> EmbeddingClient:
    if settings.GEMINI_API_KEY:
        try:
            return GeminiEmbeddingClient()
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Falling back to HashEmbeddingClient (Gemini init failed: %s)", exc
            )
    return HashEmbeddingClient()
