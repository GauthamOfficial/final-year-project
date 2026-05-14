"""ViewSets for the `attractions` app."""

from __future__ import annotations

from django.db.models import Count, Prefetch
from django.utils import timezone
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .filters import filter_attractions
from .models import Attraction, District, MediaAsset, SeasonalData
from .serializers import (
    AttractionDetailSerializer,
    AttractionListSerializer,
    DistrictSerializer,
    MediaAssetSerializer,
    SeasonalDataSerializer,
)
from .seasonal_utils import MONTH_NAMES, best_month_indices, peak_month_indices


class DistrictsPagination(PageNumberPagination):
    """Sri Lanka has 25 districts; the project default PAGE_SIZE is 20."""

    page_size = 50
    max_page_size = 200
    page_size_query_param = "page_size"


class DistrictsViewSet(viewsets.ReadOnlyModelViewSet):
    """List + retrieve districts. Aggregates a per-district attraction count."""

    permission_classes = [permissions.AllowAny]
    serializer_class = DistrictSerializer
    pagination_class = DistrictsPagination

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
            .values(
                "id",
                "name",
                "slug",
                "category",
                "sentiment_label",
                "sentiment_score",
                "positive_pct",
                "sentiment_summary",
            )
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
        seasonal_qs = SeasonalData.objects.order_by("month")
        qs = (
            Attraction.objects.select_related("district")
            .prefetch_related(
                Prefetch("media", queryset=media_qs),
                Prefetch("seasonal_data", queryset=seasonal_qs),
            )
            .all()
        )
        return filter_attractions(qs, self.request)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return AttractionDetailSerializer
        return AttractionListSerializer

    @action(detail=True, methods=["get"], url_path="sentiment")
    def sentiment(self, request, slug=None):
        attraction = self.get_object()
        if attraction.sentiment_score is None:
            return Response(
                {"message": "Sentiment not yet computed for this attraction."},
                status=404,
            )
        updated = attraction.sentiment_updated_at
        last_updated: str | None = None
        if updated is not None:
            if timezone.is_naive(updated):
                updated = timezone.make_aware(updated, timezone.get_current_timezone())
            last_updated = updated.astimezone(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
        return Response(
            {
                "attraction_id": attraction.id,
                "attraction_name": attraction.name,
                "sentiment_label": attraction.sentiment_label,
                "sentiment_score": attraction.sentiment_score,
                "positive_pct": attraction.positive_pct,
                "sentiment_summary": attraction.sentiment_summary or "",
                "last_updated": last_updated,
            }
        )

    @action(detail=True, methods=["get"], url_path="seasonal")
    def seasonal(self, request, slug=None):
        attraction = self.get_object()
        rows = list(attraction.seasonal_data.order_by("month"))
        monthly_ser = SeasonalDataSerializer(rows, many=True)
        best = best_month_indices(rows)
        peak = peak_month_indices(rows)
        return Response(
            {
                "attraction_id": attraction.id,
                "attraction_name": attraction.name,
                "best_months": best,
                "best_months_names": [MONTH_NAMES[m - 1] for m in best],
                "peak_months": peak,
                "monthly_data": monthly_ser.data,
            }
        )

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
