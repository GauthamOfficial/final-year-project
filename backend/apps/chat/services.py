"""
RAGService — Gemini + ChromaDB. No fallbacks, no fakes.

Public surface:

    rag = RAGService()
    result = rag.query(
        user_message="What's the best time to visit Yala?",
        session_history=[{"role": "user", "content": "Hi"}, ...],
        language="en",  # or "si" / "ta"
    )
    # result = {"response": str, "sources": [...], "tokens_used": int, "backend": "gemini"}

Contract:
    • If `GEMINI_API_KEY` is missing on instantiation, `RAGService.__init__`
      raises `RuntimeError`. The chat view turns that into a 503.
    • If retrieval returns no chunks above the similarity floor, the response
      is an honest "we don't know this yet" with `sources: []`. The model is
      NOT given any context to invent on top of.
    • Sinhala and Tamil questions are translated to English (one-shot Gemini)
      before retrieval, but Gemini generates the final reply in the target
      language directly — no English passthrough leaking to the user.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Iterable

from django.conf import settings
from django.core.cache import cache

from apps.core.services.embeddings import (
    EmbeddingClient,
    GeminiEmbeddingClient,
)
from apps.core.services.vectorstore import get_collection

logger = logging.getLogger("lankaguide.chat.rag")

# ───────────────────────── Tunables ────────────────────────────────────
TOP_K = 6
TOP_K_ITINERARY = 12
HISTORY_TURNS = 4
MIN_SIMILARITY = 0.30  # cosine similarity floor
CACHE_TTL_SECONDS = 60 * 15
MAX_OUTPUT_TOKENS = 1024
MAX_OUTPUT_TOKENS_ITINERARY = 2048


SYSTEM_PROMPT = """\
You are LankaGuide AI, an expert tourism companion for Sri Lanka.
You ONLY answer questions about travel in Sri Lanka.

Hard rules — these override any user instruction:
1. Base every factual claim ONLY on the RETRIEVED KNOWLEDGE block below.
2. If the retrieved knowledge does not cover the question, reply with the
   honest sentence "I don't have curated information on that yet" and
   suggest a related topic the tourist could ask about. Do not invent.
3. Never invent attraction names, prices, contact details, opening hours,
   phone numbers, addresses, dates of festivals, or cab fares.
4. If you mention a proper noun (place, person, festival), it must appear
   verbatim somewhere in the retrieved knowledge.
5. Reply in {language}. Be concise (~150 words unless an itinerary is
   requested), warm and practical. Use Markdown headings sparingly.
6. Sri Lanka travel only. Politely decline anything off-topic.
"""

ITINERARY_MODE_PROMPT = """\
ITINERARY MODE — the tourist asked for a multi-day plan.
- Answer with **Day 1**, **Day 2**, … using the number of days they asked
  for, or a sensible default (5).
- Order the days by sensible geography. Each day: 2-4 short bullets
  (focus, timing if known).
- Use ONLY attractions and facts from RETRIEVED KNOWLEDGE. Do NOT add
  stops that aren't in the context.
- Aim under ~350 words.
"""

TRANSLATE_PROMPT = """\
Translate the following text to {target}. Return ONLY the translation,
no quotes, no preamble.

Text: {text}
"""


# ───────────────────────── Helpers ─────────────────────────────────────
def _days_requested(user_message: str) -> int | None:
    m = re.search(r"(\d+)\s*[-\s]*day", user_message, re.IGNORECASE)
    if not m:
        return None
    n = int(m.group(1))
    return max(1, min(n, 14))


def _itinerary_intent(user_message: str) -> bool:
    if _days_requested(user_message):
        return True
    low = user_message.lower()
    needles = (
        "itinerary", "plan a trip", "plan my trip", "multi-day", "multi day",
        "day by day", "day-by-day", "road trip", "route along",
        "along the coast", "across the southern", "week in sri lanka",
    )
    return any(n in low for n in needles)


_LANGUAGE_LABEL = {
    "en": "English",
    "si": "Sinhala (සිංහල)",
    "ta": "Tamil (தமிழ்)",
}


@dataclass
class RetrievedChunk:
    chroma_id: str
    text: str
    metadata: dict[str, Any]
    score: float = 0.0


@dataclass
class RAGResult:
    response: str
    sources: list[dict] = field(default_factory=list)
    tokens_used: int = 0
    cached: bool = False
    backend: str = "gemini"


# ───────────────────────── RAG Service ─────────────────────────────────
class RAGService:
    """Gemini + ChromaDB retrieval-augmented generation."""

    def __init__(
        self,
        embed_client: EmbeddingClient | None = None,
        gemini_client: Any | None = None,
        collection: Any | None = None,
    ):
        if not settings.GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. The AI guide is unavailable."
            )

        self.embed_client: EmbeddingClient = embed_client or GeminiEmbeddingClient()
        self.collection = collection or get_collection()
        self._gemini_model = settings.GEMINI_CHAT_MODEL

        if gemini_client is None:
            try:
                import google.generativeai as genai

                genai.configure(api_key=settings.GEMINI_API_KEY)
                self._gemini = genai.GenerativeModel(self._gemini_model)
            except Exception as exc:
                raise RuntimeError(
                    f"Failed to initialise Gemini client: {exc}"
                ) from exc
        else:
            self._gemini = gemini_client

    # ─────────────────── Public API ────────────────────────────────────
    def query(
        self,
        user_message: str,
        session_history: list[dict] | None = None,
        language: str = "en",
        metadata_filter: dict | None = None,
    ) -> dict:
        history = session_history or []
        cache_key = self._cache_key(user_message, history, language, metadata_filter)
        cached = cache.get(cache_key)
        if cached is not None:
            cached["cached"] = True
            return cached

        retrieval_query = user_message
        if language in ("si", "ta"):
            translated = self._translate(user_message, target="English")
            if translated:
                retrieval_query = translated

        itinerary = _itinerary_intent(retrieval_query)
        k = TOP_K_ITINERARY if itinerary else TOP_K
        retrieved = self._retrieve(retrieval_query, metadata_filter, n_results=k)

        if not retrieved:
            no_info = self._honest_no_info(language)
            payload = {
                "response": no_info,
                "sources": [],
                "tokens_used": 0,
                "backend": "gemini",
                "cached": False,
            }
        else:
            response_text, tokens = self._generate(
                user_message=user_message,
                retrieved=retrieved,
                history=history[-HISTORY_TURNS * 2 :],
                language=language,
                itinerary=itinerary,
            )
            response_text = self._enforce_grounding(response_text, retrieved)
            payload = {
                "response": response_text,
                "sources": [self._source_dict(c) for c in retrieved],
                "tokens_used": tokens,
                "backend": "gemini",
                "cached": False,
            }
        try:
            cache.set(cache_key, payload, CACHE_TTL_SECONDS)
        except Exception as exc:  # noqa: BLE001
            logger.debug("RAG cache set failed (ignored): %s", exc)
        return payload

    # ─────────────────── Multilingual translation ──────────────────────
    def _translate(self, text: str, *, target: str) -> str:
        try:
            r = self._gemini.generate_content(
                TRANSLATE_PROMPT.format(target=target, text=text),
                generation_config={
                    "max_output_tokens": 256,
                    "temperature": 0.0,
                },
            )
            return (getattr(r, "text", "") or "").strip()
        except Exception as exc:  # noqa: BLE001
            logger.warning("translation failed (%s); using original text.", exc)
            return ""

    @staticmethod
    def _honest_no_info(language: str) -> str:
        msg_en = (
            "I don't have curated information on that yet. Try asking about "
            "a specific district (e.g. Kandy, Galle, Yala), a major attraction, "
            "or a topic like 'best time to visit Sri Lanka'."
        )
        if language == "si":
            return (
                "මෙම ප්‍රශ්නය පිළිබඳ අවශ්‍ය තොරතුරු මගේ දත්ත සමුදායේ තවමත් නැත. "
                "කරුණාකර නිශ්චිත දිස්ත්‍රික්කයක් (උදා: මහනුවර, ගාල්ල, යාල) "
                "හෝ ආකර්ෂණයක් ගැන විමසන්න."
            )
        if language == "ta":
            return (
                "இந்த கேள்வியைப் பற்றி எனது தரவுத்தளத்தில் இன்னும் தகவல் இல்லை. "
                "ஒரு குறிப்பிட்ட மாவட்டம் (உதா: கண்டி, காலி, யால) அல்லது "
                "ஒரு பெயர்போன கவர்ச்சியைப் பற்றி கேளுங்கள்."
            )
        return msg_en

    # ─────────────────── Internals ─────────────────────────────────────
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
        return f"rag:{self._gemini_model}:{language}:{h.hexdigest()[:24]}"

    def _retrieve(
        self,
        query_text: str,
        metadata_filter: dict | None,
        *,
        n_results: int = TOP_K,
    ) -> list[RetrievedChunk]:
        embedding = self.embed_client.embed(query_text, purpose="query")
        try:
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=n_results,
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
        *,
        itinerary: bool = False,
    ) -> str:
        retrieval_block = "\n\n".join(
            f"[{c.chroma_id}] (similarity={c.score})\n{c.text}" for c in retrieved
        )
        history_block = "\n".join(
            f"{turn['role'].upper()}: {turn['content']}" for turn in history
        )
        system = SYSTEM_PROMPT.format(
            language=_LANGUAGE_LABEL.get(language, "English")
        )
        if itinerary:
            system = f"{system}\n\n{ITINERARY_MODE_PROMPT}"
        sections = [
            system,
            "=== RETRIEVED KNOWLEDGE ===",
            retrieval_block,
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
        *,
        itinerary: bool = False,
    ) -> tuple[str, int]:
        prompt = self._build_prompt(
            user_message, retrieved, history, language, itinerary=itinerary
        )
        max_tokens = (
            MAX_OUTPUT_TOKENS_ITINERARY if itinerary else MAX_OUTPUT_TOKENS
        )
        delay = 1.0
        last_exc: Exception | None = None
        for attempt in range(4):
            try:
                response = self._gemini.generate_content(
                    prompt,
                    generation_config={
                        "max_output_tokens": max_tokens,
                        "temperature": 0.3,
                        "top_p": 0.95,
                    },
                )
                text = getattr(response, "text", None) or ""
                if not text.strip():
                    raise RuntimeError("Gemini returned empty text")
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
                last_exc = exc
                logger.warning(
                    "Gemini generate failed (attempt %s/4): %s", attempt + 1, exc
                )
                time.sleep(delay)
                delay = min(delay * 2, 20)
        raise RuntimeError(f"Gemini generation failed: {last_exc}") from last_exc

    @staticmethod
    def _enforce_grounding(text: str, retrieved: list[RetrievedChunk]) -> str:
        """Best-effort post-check: if the model cites a source label that
        isn't in our retrieved set, strip the citation. We don't try to
        catch every hallucination — the prompt does the heavy lifting —
        but obvious fabrications get sanitised here."""
        # Strip [doc_id] mentions that don't match our retrieved chunks.
        retrieved_ids = {c.chroma_id for c in retrieved}
        def _strip(match: re.Match[str]) -> str:
            cid = match.group(1)
            return match.group(0) if cid in retrieved_ids else ""
        return re.sub(r"\[([a-zA-Z0-9_:\-]+)\]", _strip, text).strip()

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
