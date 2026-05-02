"""ViewSets for the `attractions` app."""

from __future__ import annotations

from django.db.models import Count, Prefetch
from rest_framework import permissions, viewsets
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

    permission_classes = [permissions.AllowAny]
    serializer_class = DistrictSerializer

    def get_queryset(self):
        return District.objects.annotate(
            attraction_count=Count("attractions")
        ).order_by("name")

    def get_object(self):
        """Look up a district by either numeric pk or slug for friendly URLs."""
        lookup = self.kwargs.get("pk")
        qs = self.get_queryset()
        if lookup and not str(lookup).isdigit():
            obj = qs.filter(slug=lookup).first()
            if obj is None:
                obj = qs.filter(name__iexact=lookup).first()
            if obj is None:
                from django.http import Http404

                raise Http404("District not found.")
            self.check_object_permissions(self.request, obj)
            return obj
        return super().get_object()

    @action(detail=True, methods=["get"], url_path="gallery")
    def gallery(self, request, pk=None):
        """Return media + curated YouTube IDs + linked attractions for a district."""
        district = self.get_object()
        attractions = (
            Attraction.objects.filter(district=district)
            .order_by("-trend_score", "name")
            .values("id", "name", "slug", "category")
        )
        media = (
            MediaAsset.objects.filter(attraction__district=district)
            .order_by("-is_featured", "id")
            .values(
                "id",
                "type",
                "cdn_url",
                "s3_key",
                "caption",
                "attribution",
                "license",
                "source_url",
                "attraction_id",
            )[:60]
        )
        ser = self.get_serializer(district)
        return Response(
            {
                "district": ser.data,
                "attractions": list(attractions),
                "media": list(media),
            }
        )


class AttractionsViewSet(viewsets.ReadOnlyModelViewSet):
    """List + retrieve attractions, with district/category/season filters."""

    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        media_qs = MediaAsset.objects.all().order_by("-is_featured", "id")
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
        limit = int(request.query_params.get("limit", 10))
        qs = self.get_queryset().order_by("-trend_score")[:limit]
        ser = AttractionListSerializer(qs, many=True, context={"request": request})
        return Response(ser.data)


class MediaAssetsViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.AllowAny]
    serializer_class = MediaAssetSerializer

    def get_queryset(self):
        qs = MediaAsset.objects.select_related("attraction").all()
        attraction_id = self.request.query_params.get("attraction_id")
        if attraction_id and attraction_id.isdigit():
            qs = qs.filter(attraction_id=int(attraction_id))
        return qs
