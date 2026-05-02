"""Gemini-backed translation for the on-page translator."""

from __future__ import annotations

import hashlib
import logging

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger("lankaguide.translation")

_LANGUAGE_LABEL = {
    "en": "English",
    "si": "Sinhala (සිංහල)",
    "ta": "Tamil (தமிழ்)",
}

PROMPT = (
    "You are a careful translator. Translate the text below from {src} to "
    "{dst}. Preserve names, numbers, and Markdown formatting. Return ONLY "
    "the translation, no preamble, no quotes.\n\nText:\n{text}"
)

CACHE_TTL = 60 * 60 * 24


class TranslationUnavailable(RuntimeError):
    pass


def translate(text: str, *, source: str, target: str) -> str:
    if not text.strip():
        return ""
    if source == target:
        return text
    if not settings.GEMINI_API_KEY:
        raise TranslationUnavailable("GEMINI_API_KEY is not set.")
    src = _LANGUAGE_LABEL.get(source, source)
    dst = _LANGUAGE_LABEL.get(target, target)
    key = hashlib.sha256(f"{src}|{dst}|{text}".encode()).hexdigest()
    cache_key = f"translate:{key[:32]}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(settings.GEMINI_CHAT_MODEL)
        resp = model.generate_content(
            PROMPT.format(src=src, dst=dst, text=text),
            generation_config={"max_output_tokens": 1024, "temperature": 0.0},
        )
        out = (getattr(resp, "text", "") or "").strip()
        if not out:
            raise TranslationUnavailable("Empty translation.")
        try:
            cache.set(cache_key, out, CACHE_TTL)
        except Exception:
            pass
        return out
    except TranslationUnavailable:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.warning("Translation failed: %s", exc)
        raise TranslationUnavailable(str(exc)) from exc
