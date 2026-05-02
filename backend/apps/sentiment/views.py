"""
Trends API (`/api/v1/trends/`) — PRD §5.4 / §8.2.
"""

from __future__ import annotations

from django.core.cache import cache
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.attractions.models import Attraction
from apps.attractions.serializers import AttractionListSerializer

from .models import Review, ReviewSource
from .services import classify

TREND_CACHE_KEY = "trends:attractions:top"
TREND_CACHE_TTL = 60 * 60 * 6  # PRD §9.7


class TrendingAttractionsView(APIView):
    """`GET /api/v1/trends/attractions/` — top-N by trend_score."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        limit = int(request.query_params.get("limit", 12))
        cached = cache.get(TREND_CACHE_KEY)
        if cached and len(cached) >= limit:
            return Response(cached[:limit])

        qs = (
            Attraction.objects.select_related("district")
            .order_by("-trend_score")[:max(limit, 12)]
        )
        ser = AttractionListSerializer(qs, many=True, context={"request": request})
        cache.set(TREND_CACHE_KEY, ser.data, TREND_CACHE_TTL)
        return Response(ser.data[:limit])


class IngestReviewView(APIView):
    """`POST /api/v1/trends/reviews/` — manual review ingestion."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        attraction_id = request.data.get("attraction_id")
        body = (request.data.get("body") or "").strip()
        if not attraction_id or not body:
            return Response(
                {"detail": "attraction_id and body are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        result = classify(body)
        review = Review.objects.create(
            attraction_id=attraction_id,
            source=request.data.get("source", ReviewSource.MANUAL),
            external_id=request.data.get("external_id", "") or "",
            body=body,
            sentiment_score=result.score,
            sentiment_label=result.label,
        )
        return Response(
            {
                "id": review.id,
                "sentiment_score": result.score,
                "sentiment_label": result.label,
            },
            status=status.HTTP_201_CREATED,
        )
