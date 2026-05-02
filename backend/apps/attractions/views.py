"""ViewSets for the `attractions` app (PRD §8.2)."""

from __future__ import annotations

from django.db.models import Count, Prefetch
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .filters import filter_attractions
from .models import Attraction, District, MediaAsset
from .serializers import (
    AttractionDetailSerializer,
    AttractionListSerializer,
    DistrictSerializer,
    MediaAssetSerializer,
)


class DistrictsViewSet(viewsets.ReadOnlyModelViewSet):
    """List + retrieve districts. Aggregates a per-district attraction count."""

    serializer_class = DistrictSerializer

    def get_queryset(self):
        return District.objects.annotate(
            attraction_count=Count("attractions")
        ).order_by("name")


class AttractionsViewSet(viewsets.ReadOnlyModelViewSet):
    """List + retrieve attractions, with district/category/season filters.

    Supports lookup by slug (PRD §8.2 example: `/attractions/<slug>/`).
    """

    lookup_field = "slug"

    def get_queryset(self):
        media_qs = MediaAsset.objects.filter(is_featured=True)
        qs = (
            Attraction.objects.select_related("district")
            .prefetch_related(Prefetch("media", queryset=media_qs))
            .all()
        )
        return filter_attractions(qs, self.request)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return AttractionDetailSerializer
        return AttractionListSerializer

    @action(detail=False, methods=["get"], url_path="trending")
    def trending(self, request):
        """Top-N attractions sorted by `trend_score` (powers PRD §5.4)."""
        limit = int(request.query_params.get("limit", 10))
        qs = self.get_queryset().order_by("-trend_score")[:limit]
        ser = AttractionListSerializer(qs, many=True, context={"request": request})
        return Response(ser.data)


class MediaAssetsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MediaAssetSerializer

    def get_queryset(self):
        qs = MediaAsset.objects.select_related("attraction").all()
        attraction_id = self.request.query_params.get("attraction_id")
        if attraction_id and attraction_id.isdigit():
            qs = qs.filter(attraction_id=int(attraction_id))
        return qs
