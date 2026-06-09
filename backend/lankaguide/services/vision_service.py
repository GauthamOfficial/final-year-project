"""
Landmark identification via Gemini **vision** (multimodal) + optional RAG follow-up.

Images are held in memory only — never written to disk or object storage.
"""

from __future__ import annotations

import io
import json
import logging
import re
from typing import Any, BinaryIO

from django.conf import settings

from apps.attractions.models import Attraction

logger = logging.getLogger("lankaguide.vision.gemini")

PROMPT = """
You are an expert on Sri Lanka's tourist attractions and landmarks.
Look at this image carefully.

Task 1: Identify the landmark or tourist attraction shown.
Task 2: If you are confident it is a Sri Lanka landmark, provide:
  - The exact name of the landmark
  - The district it is located in
  - Your confidence level (high/medium/low)

Respond ONLY as valid JSON in this exact format:
{
  "identified": true or false,
  "landmark_name": "exact name or null",
  "district": "district name or null",
  "confidence": "high/medium/low",
  "reason": "one sentence explaining what visual features you used"
}

If this is NOT a Sri Lanka landmark or you cannot identify it with at least
medium confidence, set identified=false.
""".strip()


class VisionService:
    """Gemini vision (multimodal) + optional `RAGService` context."""

    def __init__(self) -> None:
        override = (getattr(settings, "VISION_GEMINI_MODEL", "") or "").strip()
        self._model_name = override or settings.GEMINI_CHAT_MODEL

    def identify_landmark(self, image_file: BinaryIO) -> dict[str, Any]:
        """
        Process an uploaded image file-like (Django UploadedFile).
        """
        err_base: dict[str, Any] = {
            "identified": False,
            "landmark_name": None,
            "district": None,
            "confidence": "low",
            "reason": "",
            "attraction_slug": None,
            "attraction_id": None,
            "ai_summary": None,
            "sources": None,
        }

        if not getattr(settings, "GROQ_API_KEY", ""):
            return {
                **err_base,
                "error": "AI vision is not configured. Set GROQ_API_KEY in the backend environment.",
            }

        try:
            raw = image_file.read()
            if hasattr(image_file, "seek"):
                image_file.seek(0)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Vision read failed: %s", exc)
            return {**err_base, "error": "Could not process image"}

        try:
            from PIL import Image

            img = Image.open(io.BytesIO(raw)).convert("RGB")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Vision PIL decode failed: %s", exc)
            return {**err_base, "error": "Could not process image"}

        try:
            from lankaguide.services.llm_client import get_llm

            model = get_llm("vision")
            response = model.generate_content(
                [PROMPT, img],
                generation_config={
                    "temperature": 0.2,
                    "max_output_tokens": 1024,
                },
            )
            text = _response_text_safe(response)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Groq vision failed: %s", exc)
            return {**err_base, "error": "Could not process image"}

        parsed = _parse_json_block(text)
        if not parsed:
            return {**err_base, "error": "Could not process image"}

        identified = bool(parsed.get("identified"))
        landmark_name = parsed.get("landmark_name")
        district = parsed.get("district")
        confidence = (parsed.get("confidence") or "low").lower()
        reason = str(parsed.get("reason") or "")

        out: dict[str, Any] = {
            "identified": identified,
            "landmark_name": landmark_name if landmark_name else None,
            "district": district if district else None,
            "confidence": confidence if confidence in ("high", "medium", "low") else "low",
            "reason": reason,
            "attraction_slug": None,
            "attraction_id": None,
            "ai_summary": None,
            "sources": None,
        }

        if not identified or confidence not in ("high", "medium"):
            return out

        name_key = str(landmark_name or "").strip()
        if not name_key:
            return out

        attraction = (
            Attraction.objects.filter(name__icontains=name_key)
            .order_by("-trend_score")
            .first()
        )
        if attraction is None:
            return out

        out["attraction_slug"] = attraction.slug
        out["attraction_id"] = attraction.id

        try:
            from apps.chat.services import RAGService

            rag = RAGService()
            rag_result = rag.query(
                user_message=(
                    f"Tell me about {landmark_name}: its history, significance, and visitor tips"
                ),
                session_history=[],
                language="en",
            )
            out["ai_summary"] = rag_result.get("response")
            src = rag_result.get("sources") or []
            out["sources"] = _sanitize_sources(src)
        except Exception as exc:  # noqa: BLE001
            logger.warning("RAG follow-up after vision failed: %s", exc)

        return out


def _response_text_safe(response: Any) -> str:
    """`response.text` raises ValueError when the candidate is blocked or empty."""
    try:
        raw = response.text
    except (ValueError, AttributeError) as exc:
        logger.warning("Gemini vision response text unavailable: %s", exc)
        return _extract_candidate_text(response)
    return (raw or "").strip() or _extract_candidate_text(response)


def _parse_json_block(text: str) -> dict | None:
    cleaned = re.sub(
        r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE
    ).strip()
    try:
        data = json.loads(cleaned)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                data = json.loads(m.group(0))
                return data if isinstance(data, dict) else None
            except json.JSONDecodeError:
                return None
    return None


def _extract_candidate_text(response: Any) -> str:
    """When `response.text` is empty, stitch parts from candidates."""
    parts_out: list[str] = []
    for c in getattr(response, "candidates", None) or []:
        content = getattr(c, "content", None)
        for part in getattr(content, "parts", None) or []:
            t = getattr(part, "text", None)
            if t:
                parts_out.append(t)
    return "".join(parts_out).strip()


def _sanitize_sources(sources: list[Any]) -> list[dict[str, Any]]:
    """Pass through RAG source dicts; keep JSON-serialisable primitives only."""
    safe: list[dict[str, Any]] = []
    for s in sources:
        if not isinstance(s, dict):
            continue
        row = {k: v for k, v in s.items() if v is not None}
        safe.append(row)
    return safe
