"""
Visitor sentiment for attractions: RoBERTa (Hugging Face) + **open** text sources
(OpenStreetMap / Nominatim lookup + Wikipedia extracts) + Gemini summary.
No Google Places API — fully reproducible with free ODBl / CC BY-SA content.

External HTTP is wrapped in try/except so failures never crash the caller.
Follow Nominatim usage policy: identify the app via User-Agent (see settings).
"""

from __future__ import annotations

import logging
import re
from typing import Any

import requests
from django.conf import settings
from django.utils import timezone

from apps.attractions.models import Attraction

logger = logging.getLogger("lankaguide.sentiment_service")

MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment"

# Lazy-loaded torch model state (never load at import time).
_tokenizer = None
_model = None
_torch = None


def _get_torch_model():
    """Return (tokenizer, model, torch_module) after lazy init."""
    global _tokenizer, _model, _torch
    if _model is not None and _tokenizer is not None and _torch is not None:
        return _tokenizer, _model, _torch
    try:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        _torch = torch
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        _model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
        _model.eval()
        logger.info("Loaded HF sentiment model: %s", MODEL_NAME)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to load sentiment model %s: %s", MODEL_NAME, exc)
        raise
    return _tokenizer, _model, _torch


def _split_into_snippets(
    text: str, *, max_snippets: int = 5, min_len: int = 30
) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+", text)
    out: list[str] = []
    for p in parts:
        p = p.strip()
        if len(p) >= min_len:
            out.append(p)
        if len(out) >= max_snippets:
            break
    if not out:
        chunk = text[:2000].strip()
        if chunk:
            out.append(chunk)
    return out[:max_snippets]


def _unique_snippets(snippets: list[str], cap: int = 5) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for s in snippets:
        key = s.casefold().strip()
        if len(key) < 15 or key in seen:
            continue
        seen.add(key)
        out.append(s.strip())
        if len(out) >= cap:
            break
    return out


class SentimentService:
    """Compute attraction sentiment from OSM-linked encyclopaedic text + RoBERTa."""

    def _request_headers(self) -> dict[str, str]:
        ua = getattr(
            settings,
            "NOMINATIM_USER_AGENT",
            "LankaGuide-AI/1.0 (university research; sentiment pipeline)",
        )
        return {
            "User-Agent": ua,
            "Accept": "application/json",
        }

    def _wikipedia_extract(self, title: str, lang: str = "en") -> str:
        """First section plain-text extract via MediaWiki API (no API key)."""
        title = (title or "").strip()
        if not title:
            return ""
        lang = (lang or "en").strip().lower() or "en"
        base = f"https://{lang}.wikipedia.org/w/api.php"
        try:
            r = requests.get(
                base,
                params={
                    "action": "query",
                    "format": "json",
                    "prop": "extracts",
                    "exintro": 1,
                    "explaintext": 1,
                    "redirects": 1,
                    "titles": title,
                },
                headers=self._request_headers(),
                timeout=20,
            )
            r.raise_for_status()
            data = r.json()
            pages = (data.get("query") or {}).get("pages") or {}
            for _pid, page in pages.items():
                if page.get("missing"):
                    continue
                ext = (page.get("extract") or "").strip()
                if ext:
                    return ext
        except Exception as exc:  # noqa: BLE001
            logger.debug("Wikipedia extract failed for %s:%s — %s", lang, title, exc)
        return ""

    def _nominatim_search(self, query: str) -> list[dict[str, Any]]:
        base = getattr(
            settings,
            "NOMINATIM_BASE_URL",
            "https://nominatim.openstreetmap.org",
        ).rstrip("/")
        try:
            r = requests.get(
                f"{base}/search",
                params={
                    "q": query,
                    "format": "json",
                    "limit": 5,
                    "addressdetails": 1,
                    "extratags": 1,
                },
                headers=self._request_headers(),
                timeout=20,
            )
            r.raise_for_status()
            rows = r.json()
            return rows if isinstance(rows, list) else []
        except Exception as exc:  # noqa: BLE001
            logger.warning("Nominatim search failed: %s", exc)
            return []

    def get_sentiment_text_sources(self, attraction: Attraction) -> list[str]:
        """
        Build short text snippets for RoBERTa from open data:

        1. Curated `wikipedia_title` on the attraction row (preferred).
        2. Nominatim (OSM) search → `extratags.wikipedia` / display name.
        3. Wikipedia lead section as plain text, split into sentence-like chunks.
        """
        snippets: list[str] = []
        default_lang = getattr(settings, "WIKIPEDIA_LANG", "en")

        wiki_curated = (attraction.wikipedia_title or "").strip()
        if wiki_curated:
            body = self._wikipedia_extract(wiki_curated, lang=default_lang)
            snippets.extend(
                _split_into_snippets(body, max_snippets=5, min_len=28)
            )

        query = f"{attraction.name}, {attraction.district.name}, Sri Lanka"
        results = self._nominatim_search(query)

        for row in results:
            disp = (row.get("display_name") or "").strip()
            if disp and len(disp) > 25:
                snippets.append(disp)

            extags = row.get("extratags") or {}
            wp = (extags.get("wikipedia") or "").strip()
            if wp:
                lang, title = default_lang, wp
                if ":" in wp:
                    parts = wp.split(":", 1)
                    lang = (parts[0] or default_lang).strip() or default_lang
                    title = (parts[1] or "").strip()
                if title:
                    body = self._wikipedia_extract(title, lang=lang)
                    snippets.extend(
                        _split_into_snippets(body, max_snippets=5, min_len=28)
                    )

            if len(snippets) >= 8:
                break

        # Fall back to on-record description (MySQL), encyclopaedic tone
        desc = (attraction.description or "").strip()
        if desc and len(_unique_snippets(snippets, cap=5)) < 2:
            snippets.extend(
                _split_into_snippets(desc, max_snippets=3, min_len=40)
            )

        return _unique_snippets(snippets, cap=5)

    def analyze_text(self, text: str) -> dict[str, Any]:
        """
        Use cardiffnlp/twitter-roberta-base-sentiment.
        LABEL_0=negative, LABEL_1=neutral, LABEL_2=positive.
        Score: positive=+confidence, negative=-confidence, neutral=0.
        """
        if not (text or "").strip():
            return {"label": "neutral", "score": 0.0}

        try:
            tokenizer, model, torch = _get_torch_model()
        except Exception:  # noqa: BLE001
            return {"label": "neutral", "score": 0.0}

        try:
            inputs = tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=False,
            )
            with torch.no_grad():
                logits = model(**inputs).logits
            probs = torch.softmax(logits, dim=-1)[0]
            pred = int(torch.argmax(probs).item())
            confidence = float(probs[pred].item())

            if pred == 0:
                return {"label": "negative", "score": -confidence}
            if pred == 2:
                return {"label": "positive", "score": confidence}
            return {"label": "neutral", "score": 0.0}
        except Exception as exc:  # noqa: BLE001
            logger.warning("analyze_text failed: %s", exc)
            return {"label": "neutral", "score": 0.0}

    def _gemini_summary(
        self,
        attraction_name: str,
        source_excerpts: list[str],
        overall_sentiment_label: str,
    ) -> str:
        api_key = getattr(settings, "GEMINI_API_KEY", "") or ""
        if not api_key.strip():
            return ""

        system = (
            "You are a tourism assistant. Summarize the tone of open "
            "encyclopaedic text about a Sri Lanka attraction in one friendly "
            "sentence under 20 words. Start with the attraction name."
        )
        user = (
            f"Attraction: {attraction_name}. "
            f"Source excerpts: {source_excerpts[:3]}. "
            f"RoBERTa aggregate label: {overall_sentiment_label}."
        )

        try:
            from lankaguide.services.llm_client import get_llm

            model = get_llm("fast", system_instruction=system)
            response = model.generate_content(
                user,
                generation_config={
                    "max_output_tokens": 60,
                    "temperature": 0.4,
                },
            )
            text = (getattr(response, "text", None) or "").strip()
            return text
        except Exception as exc:  # noqa: BLE001
            logger.warning("Groq summary failed: %s", exc)
            return ""

    def compute_attraction_sentiment(self, attraction_id: int) -> dict[str, Any]:
        try:
            attraction = Attraction.objects.select_related("district").get(
                pk=attraction_id
            )
        except Attraction.DoesNotExist as exc:
            raise ValueError(f"Attraction id={attraction_id} not found") from exc

        text_sources = self.get_sentiment_text_sources(attraction)

        if not text_sources:
            return {"error": "no open text sources found"}

        analyses = [self.analyze_text(t) for t in text_sources]
        scores = [float(a["score"]) for a in analyses]
        avg = sum(scores) / len(scores) if scores else 0.0

        pos_count = sum(1 for a in analyses if a.get("label") == "positive")
        positive_pct = int(round(100.0 * pos_count / len(analyses))) if analyses else 0

        if avg > 0.2:
            overall_label = "positive"
        elif avg < -0.2:
            overall_label = "negative"
        else:
            overall_label = "neutral"

        summary = self._gemini_summary(
            attraction.name,
            text_sources,
            overall_label,
        )

        now = timezone.now()
        attraction.sentiment_score = avg
        attraction.sentiment_label = overall_label
        attraction.sentiment_summary = summary or ""
        attraction.sentiment_updated_at = now
        attraction.positive_pct = positive_pct
        attraction.save(
            update_fields=[
                "sentiment_score",
                "sentiment_label",
                "sentiment_summary",
                "sentiment_updated_at",
                "positive_pct",
            ]
        )

        return {
            "attraction_id": attraction.id,
            "attraction_name": attraction.name,
            "sentiment_label": attraction.sentiment_label,
            "sentiment_score": attraction.sentiment_score,
            "positive_pct": attraction.positive_pct,
            "sentiment_summary": attraction.sentiment_summary,
            "last_updated": attraction.sentiment_updated_at,
        }