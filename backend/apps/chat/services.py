"""
RAGService — Gemini + ChromaDB + Redis (Prompt 4A, PRD §9.2-§9.7).

Public surface:

    rag = RAGService()
    result = rag.query(
        user_message="What's the best time to visit Yala?",
        session_history=[{"role": "user", "content": "Hi"}, ...],
        language="en",
    )
    # result = {"response": "...", "sources": [...], "tokens_used": 312}

Resilience contract:
    • No GEMINI_API_KEY  → use HashEmbeddingClient + extractive synthesis.
    • Redis unreachable  → bypass the cache (django-redis IGNORE_EXCEPTIONS).
    • ChromaDB empty     → return a polite "no info" response with no sources.

The prompt structure follows PRD §9.3 verbatim; tweaks live in the constants
near the top of this module so changes are reviewable in one place.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Iterable

from django.conf import settings
from django.core.cache import cache

from apps.core.services.embeddings import (
    EmbeddingClient,
    GeminiEmbeddingClient,
    HashEmbeddingClient,
    get_embedding_client,
)
from apps.core.services.vectorstore import get_collection

logger = logging.getLogger("lankaguide.chat.rag")


# ───────────────────────── Tunables ────────────────────────────────────
TOP_K = 5
HISTORY_TURNS = 4
MIN_SIMILARITY = 0.20  # cosine similarity floor (PRD §14.2)
CACHE_TTL_SECONDS = 60 * 15  # PRD §9.7
MAX_OUTPUT_TOKENS = 1024  # PRD §9.6


SYSTEM_PROMPT = """\
You are LankaGuide AI, an expert tourism companion for Sri Lanka.
You ONLY answer questions about travel in Sri Lanka.
You MUST base all factual claims on the CONTEXT provided below.
If the context does not contain enough information, say so clearly.
Do NOT invent attraction names, prices, or contact details.
Respond in {language}. Be concise, friendly, and practical.
"""

NO_CONTEXT_FALLBACK = (
    "I do not yet have curated information about that topic in my Sri Lanka "
    "knowledge base. You can rephrase, ask about a different attraction, or "
    "check the official Sri Lanka Tourism Development Authority for the "
    "latest details."
)


@dataclass
class RetrievedChunk:
    chroma_id: str
    text: str
    metadata: dict[str, Any]
    score: float = 0.0  # similarity (1.0 = identical)


@dataclass
class RAGResult:
    response: str
    sources: list[dict] = field(default_factory=list)
    tokens_used: int = 0
    cached: bool = False
    backend: str = "stub"


# ───────────────────────── RAG Service ─────────────────────────────────
class RAGService:
    """
    Single-instance preferred — share via dependency injection or lru_cache
    to avoid reopening ChromaDB / re-initialising the Gemini client on every
    request.
    """

    def __init__(
        self,
        embed_client: EmbeddingClient | None = None,
        gemini_client: Any | None = None,
        collection: Any | None = None,
    ):
        self.embed_client: EmbeddingClient = embed_client or get_embedding_client()
        self.collection = collection or get_collection()
        self._gemini = gemini_client
        self._gemini_model = settings.GEMINI_CHAT_MODEL

        if self._gemini is None and settings.GEMINI_API_KEY:
            try:
                import google.generativeai as genai

                genai.configure(api_key=settings.GEMINI_API_KEY)
                self._gemini = genai.GenerativeModel(self._gemini_model)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Gemini init failed (%s); using extractive fallback.", exc)
                self._gemini = None

        self._is_offline = (
            isinstance(self.embed_client, HashEmbeddingClient) and self._gemini is None
        )

    # ─────────────────── Public API ────────────────────────────────────
    def query(
        self,
        user_message: str,
        session_history: list[dict] | None = None,
        language: str = "en",
        metadata_filter: dict | None = None,
    ) -> dict:
        """Main entry point. Returns the dict shape consumed by `chat` views."""
        history = session_history or []
        cache_key = self._cache_key(user_message, history, language, metadata_filter)
        cached = cache.get(cache_key)
        if cached is not None:
            logger.debug("RAG cache hit: %s", cache_key)
            cached["cached"] = True
            return cached

        retrieved = self._retrieve(user_message, metadata_filter)
        if not retrieved:
            result = RAGResult(
                response=NO_CONTEXT_FALLBACK,
                sources=[],
                tokens_used=0,
                backend=self._backend_name(),
            )
        else:
            response_text, tokens = self._generate(
                user_message=user_message,
                retrieved=retrieved,
                history=history[-HISTORY_TURNS * 2 :],
                language=language,
            )
            result = RAGResult(
                response=response_text,
                sources=[self._source_dict(c) for c in retrieved],
                tokens_used=tokens,
                backend=self._backend_name(),
            )

        payload = {
            "response": result.response,
            "sources": result.sources,
            "tokens_used": result.tokens_used,
            "backend": result.backend,
            "cached": False,
        }
        try:
            cache.set(cache_key, payload, CACHE_TTL_SECONDS)
        except Exception as exc:  # noqa: BLE001
            logger.debug("RAG cache set failed (ignored): %s", exc)
        return payload

    # ─────────────────── Internals ─────────────────────────────────────
    def _backend_name(self) -> str:
        if isinstance(self.embed_client, GeminiEmbeddingClient) and self._gemini:
            return "gemini"
        if self._gemini:
            return "gemini-llm-only"
        return "extractive-offline"

    def _cache_key(
        self,
        user_message: str,
        history: list[dict],
        language: str,
        metadata_filter: dict | None,
    ) -> str:
        h = hashlib.sha256()
        h.update(user_message.encode("utf-8"))
        h.update(json.dumps(history, sort_keys=True).encode("utf-8"))
        h.update(language.encode("utf-8"))
        h.update(json.dumps(metadata_filter or {}, sort_keys=True).encode("utf-8"))
        return f"rag:{self._gemini_model}:{h.hexdigest()[:24]}"

    def _retrieve(
        self, query_text: str, metadata_filter: dict | None
    ) -> list[RetrievedChunk]:
        embedding = self.embed_client.embed(query_text)
        try:
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=TOP_K,
                where=metadata_filter or None,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("ChromaDB query failed (%s) — returning no chunks.", exc)
            return []

        chunks: list[RetrievedChunk] = []
        ids = (results.get("ids") or [[]])[0]
        docs = (results.get("documents") or [[]])[0]
        metas = (results.get("metadatas") or [[]])[0]
        distances = (results.get("distances") or [[None] * len(ids)])[0]

        for cid, doc, meta, dist in zip(ids, docs, metas, distances):
            # ChromaDB cosine distance ∈ [0, 2]; similarity = 1 - distance/2.
            similarity = (1.0 - (dist / 2.0)) if dist is not None else 1.0
            if similarity < MIN_SIMILARITY:
                continue
            chunks.append(
                RetrievedChunk(
                    chroma_id=cid,
                    text=doc or "",
                    metadata=meta or {},
                    score=round(similarity, 4),
                )
            )
        return chunks

    def _build_prompt(
        self,
        user_message: str,
        retrieved: Iterable[RetrievedChunk],
        history: list[dict],
        language: str,
    ) -> str:
        """Four-part prompt assembly (PRD §9.3)."""

        retrieval_block = "\n\n".join(
            f"[{c.chroma_id}] (similarity={c.score})\n{c.text}" for c in retrieved
        )
        history_block = "\n".join(
            f"{turn['role'].upper()}: {turn['content']}" for turn in history
        )

        sections = [
            SYSTEM_PROMPT.format(language=_LANGUAGE_LABEL.get(language, "English")),
            "=== RETRIEVED KNOWLEDGE ===",
            retrieval_block or "(no context returned)",
            "=== END RETRIEVED KNOWLEDGE ===",
        ]
        if history_block:
            sections += [
                "=== PREVIOUS CONVERSATION ===",
                history_block,
                "=== END CONVERSATION ===",
            ]
        sections.append(f"Tourist Question: {user_message}")
        return "\n\n".join(sections)

    def _generate(
        self,
        user_message: str,
        retrieved: list[RetrievedChunk],
        history: list[dict],
        language: str,
    ) -> tuple[str, int]:
        prompt = self._build_prompt(user_message, retrieved, history, language)

        if self._gemini is None:
            # Extractive synthesis — works offline. Concatenates the highest
            # scoring chunk and tags the source for transparency.
            top = retrieved[0]
            response_text = (
                f"Based on curated Sri Lanka tourism notes, here's what I have:\n\n"
                f"{top.text}\n\n"
                f"_(Offline mode — set GEMINI_API_KEY to enable LLM rewriting.)_"
            )
            return response_text, len(response_text.split())

        delay = 1.0
        for attempt in range(4):
            try:
                response = self._gemini.generate_content(
                    prompt,
                    generation_config={
                        "max_output_tokens": MAX_OUTPUT_TOKENS,
                        "temperature": 0.4,
                        "top_p": 0.95,
                    },
                )
                text = getattr(response, "text", None) or ""
                tokens = 0
                meta = getattr(response, "usage_metadata", None)
                if meta is not None:
                    tokens = (
                        getattr(meta, "total_token_count", 0)
                        or getattr(meta, "prompt_token_count", 0)
                        + getattr(meta, "candidates_token_count", 0)
                    )
                return text.strip(), int(tokens)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Gemini generate failed (attempt %s/4): %s", attempt + 1, exc
                )
                time.sleep(delay)
                delay = min(delay * 2, 20)
        # Final fallback — return the first chunk extractively.
        return retrieved[0].text, 0

    @staticmethod
    def _source_dict(chunk: RetrievedChunk) -> dict:
        meta = chunk.metadata or {}
        title = meta.get("slug") or meta.get("source_filename") or chunk.chroma_id
        return {
            "doc_id": chunk.chroma_id,
            "title": title,
            "relevance": chunk.score,
            "attraction_id": meta.get("attraction_id"),
            "district_id": meta.get("district_id"),
            "category": meta.get("category"),
        }


_LANGUAGE_LABEL = {
    "en": "English",
    "si": "Sinhala (සිංහල)",
    "ta": "Tamil (தமிழ்)",
}
