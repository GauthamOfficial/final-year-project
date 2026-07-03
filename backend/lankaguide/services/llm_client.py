"""
Unified LLM client — wraps the **Groq** API behind a thin adapter that
mirrors the ``generate_content()`` call signature previously used with
``google.generativeai.GenerativeModel``.

This lets every service swap one import line and keep all existing
generation calls unchanged.

Usage::

    from lankaguide.services.llm_client import get_llm

    model = get_llm("chat")          # openai/gpt-oss-120b
    model = get_llm("fast")          # llama-3.1-8b-instant
    model = get_llm("vision")        # llama-4-scout (multimodal)

    response = model.generate_content(
        "Tell me about Sigiriya",
        generation_config={"temperature": 0.4, "max_output_tokens": 512},
    )
    print(response.text)
"""

from __future__ import annotations

import base64
import io
import logging
from dataclasses import dataclass, field
from typing import Any

from django.conf import settings

logger = logging.getLogger("lankaguide.llm_client")

# ─────────────────────── Response wrappers ────────────────────────────
# Mirror the attributes that existing code reads off a Gemini response.


@dataclass
class _UsageMeta:
    prompt_token_count: int = 0
    candidates_token_count: int = 0
    total_token_count: int = 0


@dataclass
class _Part:
    text: str = ""


@dataclass
class _Content:
    parts: list[_Part] = field(default_factory=list)


@dataclass
class _Candidate:
    content: _Content = field(default_factory=_Content)


class GroqResponse:
    """Drop-in for ``google.generativeai`` response objects."""

    def __init__(self, text: str, usage: _UsageMeta | None = None):
        self._text = text
        self.usage_metadata = usage or _UsageMeta()
        self.candidates = [
            _Candidate(content=_Content(parts=[_Part(text=text)]))
        ]

    @property
    def text(self) -> str:
        return self._text


# ─────────────────────── Adapter ──────────────────────────────────────


class GroqGenerativeModel:
    """
    Wraps :pypi:`groq` so callers can keep the Gemini-style
    ``model.generate_content(prompt, generation_config={...})`` pattern.
    """

    def __init__(
        self,
        model_name: str,
        *,
        api_key: str = "",
        system_instruction: str | None = None,
    ):
        from groq import Groq  # lazy so import errors surface at call time

        self._model = model_name
        self._system = system_instruction
        self._client = Groq(api_key=api_key or settings.GROQ_API_KEY)

    # ── public interface ──────────────────────────────────────────────

    def generate_content(
        self,
        prompt: str | list,
        *,
        generation_config: dict[str, Any] | None = None,
    ) -> GroqResponse:
        """
        Parameters
        ----------
        prompt
            A plain string, **or** a list ``[text, PIL.Image]`` for vision.
        generation_config
            Keys understood (mapped to Groq equivalents):
            - ``max_output_tokens`` → ``max_tokens``
            - ``temperature``
            - ``top_p``
            - ``response_mime_type``  ``"application/json"`` →
              ``response_format={"type": "json_object"}``
        """
        cfg = generation_config or {}
        messages: list[dict[str, Any]] = []

        # System message
        if self._system:
            messages.append({"role": "system", "content": self._system})

        # Build user message — may be multimodal
        messages.append(self._build_user_message(prompt))

        # Map generation_config → Groq kwargs
        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
        }
        if "max_output_tokens" in cfg:
            kwargs["max_tokens"] = cfg["max_output_tokens"]
        if "temperature" in cfg:
            kwargs["temperature"] = cfg["temperature"]
        if "top_p" in cfg:
            kwargs["top_p"] = cfg["top_p"]
        if cfg.get("response_mime_type") == "application/json":
            kwargs["response_format"] = {"type": "json_object"}

        try:
            completion = self._client.chat.completions.create(**kwargs)
        except Exception:
            logger.exception("Groq API call failed (model=%s)", self._model)
            raise

        text = (completion.choices[0].message.content or "").strip()
        usage = _UsageMeta(
            prompt_token_count=getattr(completion.usage, "prompt_tokens", 0),
            candidates_token_count=getattr(
                completion.usage, "completion_tokens", 0
            ),
            total_token_count=getattr(completion.usage, "total_tokens", 0),
        )
        return GroqResponse(text=text, usage=usage)

    # ── internals ─────────────────────────────────────────────────────

    @staticmethod
    def _build_user_message(prompt: str | list) -> dict[str, Any]:
        """Handle plain text or ``[text, PIL.Image]`` vision input."""
        if isinstance(prompt, str):
            return {"role": "user", "content": prompt}

        # Vision: list of [text, PIL.Image, ...]
        content_parts: list[dict[str, Any]] = []
        for item in prompt:
            if isinstance(item, str):
                content_parts.append({"type": "text", "text": item})
            else:
                # Assume PIL Image (or anything with a save method)
                content_parts.append(
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": _pil_to_data_url(item),
                        },
                    }
                )
        return {"role": "user", "content": content_parts}


def _pil_to_data_url(img: Any) -> str:
    """Convert a PIL Image to a base64 data URL."""
    buf = io.BytesIO()
    fmt = getattr(img, "format", None) or "JPEG"
    img.save(buf, format=fmt)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    mime = f"image/{fmt.lower()}"
    return f"data:{mime};base64,{b64}"


# ─────────────────────── Factory ──────────────────────────────────────

_MODEL_KEYS = {
    "chat": lambda: getattr(settings, "GROQ_CHAT_MODEL", "openai/gpt-oss-120b"),
    "fast": lambda: getattr(settings, "GROQ_FAST_MODEL", "llama-3.1-8b-instant"),
    "vision": lambda: getattr(
        settings, "GROQ_VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct"
    ),
    "itinerary": lambda: getattr(
        settings, "GROQ_ITINERARY_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct"
    ),
}


def get_llm(
    model_key: str = "chat",
    *,
    system_instruction: str | None = None,
) -> GroqGenerativeModel:
    """
    Return a configured :class:`GroqGenerativeModel`.

    Parameters
    ----------
    model_key
        ``"chat"`` (70B versatile), ``"fast"`` (8B instant),
        or ``"vision"`` (multimodal).
    system_instruction
        Optional system-level instruction prepended to every request.
    """
    api_key = getattr(settings, "GROQ_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured. Set it in your .env file. "
            "Get a free key at https://console.groq.com"
        )
    resolver = _MODEL_KEYS.get(model_key)
    if resolver is None:
        raise ValueError(
            f"Unknown model_key {model_key!r}. Choose from: {list(_MODEL_KEYS)}"
        )
    model_name = resolver()
    return GroqGenerativeModel(
        model_name,
        api_key=api_key,
        system_instruction=system_instruction,
    )
