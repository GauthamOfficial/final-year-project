"""
Itinerary endpoints (PRD §5.2, §8.2, §8.3).

`POST /api/v1/itinerary/generate/` constructs an itinerary using the
`ItineraryService` (Prompt 4B). Until that lands, a deterministic stub keeps
the UI flow exercisable end-to-end.
"""

from __future__ import annotations

import logging

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.attractions.models import Attraction
from apps.core.models import Visitor

from .models import Itinerary, ItineraryDay, ItineraryStatus, ItineraryStop
from .serializers import (
    GenerateItineraryRequestSerializer,
    ItinerarySerializer,
)

logger = logging.getLogger("lankaguide.itinerary")


def _resolve_visitor(request) -> Visitor:
    token = request.headers.get("X-Session-Token") or ""
    visitor, _ = Visitor.get_or_create_by_token(token)
    return visitor


def _stub_generate(visitor: Visitor, prefs: dict) -> Itinerary:
    """
    Fallback used when `ItineraryService` is unavailable. Picks attractions
    that match the requested districts/categories so the response shape is
    populated correctly even without Gemini access.
    """
    qs = Attraction.objects.filter(
        district_id__in=prefs["district_ids"],
        category__in=prefs["interests"],
    ).order_by("-trend_score")
    pool = list(qs[: max(prefs["num_days"] * 3, 6)])

    itinerary = Itinerary.objects.create(
        visitor=visitor,
        title=prefs.get("title")
        or f"{prefs['num_days']}-Day Sri Lanka Itinerary",
        start_date=prefs["start_date"],
        end_date=prefs["end_date"],
        budget_lkr=prefs["budget_lkr"],
        group_type=prefs["group_type"],
        group_size=prefs["group_size"],
        status=ItineraryStatus.DRAFT,
    )

    for day_idx in range(prefs["num_days"]):
        day_attractions = pool[day_idx * 3 : day_idx * 3 + 3] or pool[:3]
        district = day_attractions[0].district if day_attractions else None
        day = ItineraryDay.objects.create(
            itinerary=itinerary,
            day_number=day_idx + 1,
            district=district,
            notes="(stub) ItineraryService not configured — RAG-grounded itinerary lands in Prompt 4B.",
            ai_generated=False,
        )
        for order, att in enumerate(day_attractions, start=1):
            ItineraryStop.objects.create(
                day=day,
                attraction=att,
                stop_order=order,
                duration_mins=90,
                tip="Arrive early to avoid crowds; check seasonal opening hours.",
            )

    return itinerary


class GenerateItineraryView(APIView):
    """`POST /api/v1/itinerary/generate/`."""

    def post(self, request):
        ser = GenerateItineraryRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        prefs = ser.validated_data

        visitor = _resolve_visitor(request)

        try:
            from apps.itinerary.services import ItineraryService

            itinerary = ItineraryService().generate(visitor=visitor, preferences=prefs)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "ItineraryService unavailable, falling back to stub: %s", exc
            )
            itinerary = _stub_generate(visitor, prefs)

        out = ItinerarySerializer(itinerary)
        return Response(out.data, status=status.HTTP_201_CREATED)


class ItineraryViewSet(viewsets.ReadOnlyModelViewSet):
    """`GET /api/v1/itinerary/{id}/` and `…/by_share/{token}/`."""

    serializer_class = ItinerarySerializer

    def get_queryset(self):
        visitor = _resolve_visitor(self.request)
        return (
            Itinerary.objects.filter(visitor=visitor)
            .prefetch_related("days__stops__attraction")
            .order_by("-created_at")
        )

    @action(
        detail=False,
        methods=["get"],
        url_path=r"by_share/(?P<token>[^/]+)",
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
        """`PATCH .../day/{day_num}/regenerate/` — wired to ItineraryService."""
        try:
            itinerary = self.get_queryset().get(pk=pk)
        except Itinerary.DoesNotExist:
            return Response(
                {"detail": "Itinerary not found."}, status=status.HTTP_404_NOT_FOUND
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
            return Response(
                {"detail": "Regeneration failed; try again later."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        itinerary.refresh_from_db()
        return Response(ItinerarySerializer(itinerary).data)
