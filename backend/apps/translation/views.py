"""`POST /api/v1/translate/` — { text, source, target }."""

from __future__ import annotations

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import TranslationUnavailable, translate

LANGS = {"en", "si", "ta"}


class TranslateView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        text = (request.data.get("text") or "").strip()
        source = (request.data.get("source") or "auto").strip()
        target = (request.data.get("target") or "en").strip()
        if not text:
            return Response(
                {"detail": "text is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if target not in LANGS:
            return Response(
                {"detail": f"target must be one of {sorted(LANGS)}."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(text) > 4000:
            return Response(
                {"detail": "text must be 4000 characters or fewer."},
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )
        try:
            translation = translate(text, source=source, target=target)
        except TranslationUnavailable as exc:
            return Response(
                {"detail": str(exc), "code": "translation_unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(
            {"translation": translation, "source": source, "target": target}
        )
