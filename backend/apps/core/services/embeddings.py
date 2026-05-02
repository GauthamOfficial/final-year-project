"""
Embedding clients for the RAG pipeline (PRD §9.1.2 → §9.2).

**Primary:** `google-genai` (`google.genai`) with `gemini-embedding-001` and
`output_dimensionality=768`. The older `google.generativeai.embed_content` path
often returns **404** on current Generative Language API keys — do not use it
for new deployments.

**Offline / tests:** `HashEmbeddingClient` — deterministic 768-d vectors.
"""

from __future__ import annotations

import hashlib
import logging
import math
import os
import struct
import time
from typing import Literal, Sequence

from django.conf import settings

logger = logging.getLogger("lankaguide.core.embeddings")

EMBEDDING_DIM = 768  # Must match `output_dimensionality` for Gemini embeddings


class EmbeddingClient:
    name: str = "base"
    dimension: int = EMBEDDING_DIM

    def embed(
        self, text: str, *, purpose: Literal["query", "document"] = "query"
    ) -> list[float]:
        raise NotImplementedError

    def embed_batch(
        self,
        texts: Sequence[str],
        *,
        purpose: Literal["query", "document"] = "query",
    ) -> list[list[float]]:
        return [self.embed(t, purpose=purpose) for t in texts]


class HashEmbeddingClient(EmbeddingClient):
    """
    Deterministic offline embedding (SHA-512-derived, 768-d, unit-norm).
    """

    name = "hash-deterministic"

    def embed(
        self, text: str, *, purpose: Literal["query", "document"] = "query"
    ) -> list[float]:
        _ = purpose
        seed = hashlib.sha512(text.encode("utf-8")).digest()
        floats: list[float] = []
        i = 0
        while len(floats) < self.dimension:
            chunk = hashlib.sha512(seed + i.to_bytes(2, "big")).digest()
            for offset in range(0, len(chunk), 4):
                if len(floats) >= self.dimension:
                    break
                (raw,) = struct.unpack("I", chunk[offset : offset + 4])
                floats.append((raw / 0xFFFFFFFF) * 2 - 1)
            i += 1
        norm = math.sqrt(sum(x * x for x in floats)) or 1.0
        return [x / norm for x in floats]


def _normalize_embedding_model(name: str) -> str:
    """
    Map legacy / PRD names to IDs that work on the current Gemini API
    (google-genai, ML Dev).
    """
    n = (name or "").strip()
    if n.startswith("models/"):
        n = n[7:]
    # Old SDK defaults & PRD names → current embedding model
    legacy = {
        "embedding-001": "gemini-embedding-001",
        "text-embedding-004": "gemini-embedding-001",
    }
    return legacy.get(n, n) or "gemini-embedding-001"


def _task_type(purpose: Literal["query", "document"]) -> str:
    return (
        "RETRIEVAL_QUERY" if purpose == "query" else "RETRIEVAL_DOCUMENT"
    )


class GeminiEmbeddingClient(EmbeddingClient):
    """Gemini embeddings via `google-genai` (not deprecated `google.generativeai`)."""

    name = "gemini"

    def __init__(self, model: str | None = None, max_retries: int = 5):
        from google import genai
        from google.genai import types as genai_types

        api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set; cannot use GeminiEmbeddingClient.")
        self._client = genai.Client(api_key=api_key)
        raw = model or settings.GEMINI_EMBEDDING_MODEL
        self.model = _normalize_embedding_model(raw)
        self.max_retries = max_retries
        self._EmbedContentConfig = genai_types.EmbedContentConfig

    def _embed_once(
        self, text: str, *, purpose: Literal["query", "document"]
    ) -> list[float]:
        cfg = self._EmbedContentConfig(
            output_dimensionality=EMBEDDING_DIM,
            task_type=_task_type(purpose),
        )
        resp = self._client.models.embed_content(
            model=self.model,
            contents=text,
            config=cfg,
        )
        embs = resp.embeddings
        if not embs or not embs[0].values:
            raise RuntimeError("Gemini returned no embedding values")
        return list(embs[0].values)

    def embed(
        self, text: str, *, purpose: Literal["query", "document"] = "query"
    ) -> list[float]:
        delay = 1.0
        last_exc: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                return self._embed_once(text, purpose=purpose)
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
        raise RuntimeError(
            f"Gemini embed failed after {self.max_retries} retries"
        ) from last_exc


def get_embedding_client() -> EmbeddingClient:
    """Return a real Gemini embedding client. Raises if not configured.

    The deterministic HashEmbeddingClient is retained in this module purely
    as a fixture for unit tests; we never silently fall back to it for real
    user requests.
    """
    if not settings.GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. Set it in the backend env "
            "to enable real embeddings."
        )
    return GeminiEmbeddingClient()
