"""
Vision endpoints (PRD §5.3, §8.2 / §8.3).

POST /api/v1/vision/identify/
  multipart/form-data:
    image=<binary>
"""

from __future__ import annotations

import logging

from rest_framework import permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger("lankaguide.vision.views")


class IdentifyView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        image = request.FILES.get("image")
        if not image:
            return Response(
                {"detail": "Multipart field 'image' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if image.size > 8 * 1024 * 1024:
            return Response(
                {"detail": "Image must be smaller than 8 MB."},
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )

        try:
            from apps.vision.services import VisionService

            result = VisionService().identify(image)
        except Exception as exc:  # noqa: BLE001
            logger.exception("VisionService crashed: %s", exc)
            return Response(
                {"detail": "Vision pipeline unavailable; try again later."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(result, status=status.HTTP_200_OK)
