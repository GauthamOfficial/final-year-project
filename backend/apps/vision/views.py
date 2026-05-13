"""
Vision endpoints — landmark identification via Gemini vision.

POST /api/v1/vision/identify/
  multipart/form-data:
    image=<binary>
"""

from __future__ import annotations

import logging
import time

from django.core.cache import cache
from rest_framework import permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from lankaguide.services.vision_service import VisionService

logger = logging.getLogger("lankaguide.vision.views")

_MAX_BYTES = 10 * 1024 * 1024
_HOUR = 3600
_ALLOWED_CT = frozenset(
    {
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/webp",
    }
)


def _client_ip(request) -> str:
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR") or "unknown"


def _vision_rate_limit_key(request) -> str:
    bucket = int(time.time() // _HOUR)
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        return f"vision:identify:{bucket}:u:{user.pk}"
    session = getattr(request, "session", None)
    sid = getattr(session, "session_key", None) or ""
    if sid:
        return f"vision:identify:{bucket}:s:{sid}"
    return f"vision:identify:{bucket}:ip:{_client_ip(request)}"


def _vision_rate_allow(request) -> bool:
    """At most 10 successful vision calls per bucket per session / user / IP."""
    key = _vision_rate_limit_key(request)
    try:
        n = cache.get(key)
        if n is None:
            cache.set(key, 1, _HOUR + 120)
            return True
        if n >= 10:
            return False
        cache.incr(key)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Vision rate-limit cache error (allowing): %s", exc)
        return True


class VisionIdentifyView(APIView):
    """Multipart upload → Gemini vision + optional RAG. Images stay in memory only."""

    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        image = request.FILES.get("image")
        if not image:
            return Response(
                {"error": "No image provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if getattr(image, "size", 0) > _MAX_BYTES:
            return Response(
                {"error": "File too large. Maximum size is 10MB."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ct = (getattr(image, "content_type", "") or "").lower().strip()
        if ct not in _ALLOWED_CT:
            _peek = image.read(32 * 1024)
            if hasattr(image, "seek"):
                image.seek(0)
            ok_magic = False
            if _peek.startswith(b"\xff\xd8\xff"):
                ok_magic = True
            elif _peek[:8] == b"\x89PNG\r\n\x1a\n":
                ok_magic = True
            elif _peek[:4] == b"RIFF" and _peek[8:12] == b"WEBP":
                ok_magic = True
            if not ok_magic:
                return Response(
                    {
                        "error": "Invalid file type. Please upload JPG, PNG, or WEBP."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if not _vision_rate_allow(request):
            return Response(
                {
                    "error": "Rate limit exceeded. Maximum 10 identifications per hour."
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        try:
            result = VisionService().identify_landmark(image)
        except Exception as exc:  # noqa: BLE001
            logger.exception("VisionService crashed: %s", exc)
            return Response(
                {"identified": False, "error": "Could not process image"},
                status=status.HTTP_200_OK,
            )

        return Response(result, status=status.HTTP_200_OK)
