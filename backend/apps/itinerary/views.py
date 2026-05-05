"""Itinerary endpoints — owned by the authenticated user."""

from __future__ import annotations

import logging

from django.conf import settings
from django.http import HttpResponse
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Itinerary
from .pdf import render_itinerary_pdf
from .serializers import (
    GenerateItineraryRequestSerializer,
    ItinerarySerializer,
)

logger = logging.getLogger("lankaguide.itinerary")


def _service_unavailable(message: str) -> Response:
    return Response(
        {"detail": message, "code": "service_unavailable"},
        status=status.HTTP_503_SERVICE_UNAVAILABLE,
    )


class GenerateItineraryView(APIView):
    """`POST /api/v1/itinerary/generate/`."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        ser = GenerateItineraryRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        prefs = ser.validated_data

        if not getattr(settings, "GEMINI_API_KEY", ""):
            return _service_unavailable(
                "AI itinerary planner is not configured. Set GEMINI_API_KEY."
            )

        try:
            from apps.itinerary.services import ItineraryService

            itinerary = ItineraryService().generate(user=request.user, preferences=prefs)
        except RuntimeError as exc:
            return _service_unavailable(str(exc))
        except Exception as exc:  # noqa: BLE001
            logger.exception("Itinerary generation failed: %s", exc)
            return _service_unavailable(
                "Itinerary planner is temporarily unavailable. Please retry shortly."
            )

        out = ItinerarySerializer(itinerary)
        return Response(out.data, status=status.HTTP_201_CREATED)


class ItineraryViewSet(viewsets.ReadOnlyModelViewSet):
    """`GET /api/v1/itinerary/` and `…/by_share/{token}/`."""

    serializer_class = ItinerarySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Itinerary.objects.filter(user=self.request.user)
            .prefetch_related("days__stops__attraction")
            .order_by("-created_at")
        )

    @action(
        detail=False,
        methods=["get"],
        url_path=r"by_share/(?P<token>[^/]+)",
        permission_classes=[permissions.AllowAny],
    )
    def by_share(self, request, token: str = ""):
        try:
            itinerary = Itinerary.objects.prefetch_related(
                "days__stops__attraction"
            ).get(share_token=token)
        except Itinerary.DoesNotExist:
            return Response(
                {"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(ItinerarySerializer(itinerary).data)

    @action(
        detail=True,
        methods=["patch"],
        url_path=r"day/(?P<day_num>\d+)/regenerate",
    )
    def regenerate_day(self, request, slug=None, pk=None, day_num: str = "1"):
        try:
            itinerary = self.get_queryset().get(pk=pk)
        except Itinerary.DoesNotExist:
            return Response(
                {"detail": "Itinerary not found."}, status=status.HTTP_404_NOT_FOUND
            )

        if not getattr(settings, "GEMINI_API_KEY", ""):
            return _service_unavailable(
                "AI itinerary planner is not configured."
            )

        try:
            from apps.itinerary.services import ItineraryService

            ItineraryService().regenerate_day(
                itinerary=itinerary, day_number=int(day_num)
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:  # noqa: BLE001
            logger.warning("regenerate_day failed: %s", exc)
            return _service_unavailable(
                "Regeneration failed; try again later."
            )

        itinerary.refresh_from_db()
        return Response(ItinerarySerializer(itinerary).data)

    @action(detail=True, methods=["delete"], url_path="delete")
    def delete_itinerary(self, request, pk=None):
        itinerary = self.get_object()
        itinerary.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=["get"],
        url_path="pdf",
        permission_classes=[permissions.AllowAny],
    )
    def pdf(self, request, pk=None):
        """`GET /api/v1/itinerary/{id}/pdf/` — bytes/pdf.

        Owner can always download. Anyone with the share token may also
        download by appending `?token=<share_token>`.
        """
        try:
            itinerary = Itinerary.objects.prefetch_related(
                "days__stops__attraction", "days__district"
            ).get(pk=pk)
        except Itinerary.DoesNotExist:
            return Response(
                {"detail": "Itinerary not found."}, status=status.HTTP_404_NOT_FOUND
            )

        token = request.query_params.get("token", "")
        is_owner = (
            request.user.is_authenticated and itinerary.user_id == request.user.id
        )
        is_shared = token and token == itinerary.share_token
        if not (is_owner or is_shared):
            return Response(
                {"detail": "Sign in or use a valid share token."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            pdf_bytes = render_itinerary_pdf(itinerary)
        except Exception as exc:  # noqa: BLE001
            logger.exception("PDF render failed: %s", exc)
            return Response(
                {"detail": "PDF generation failed."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        filename = f"lankaguide-itinerary-{itinerary.id}.pdf"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
