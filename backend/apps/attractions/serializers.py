"""DRF serializers for the `attractions` app (PRD §8.2)."""

from __future__ import annotations

from rest_framework import serializers

from .models import Attraction, District, MediaAsset


class MediaAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaAsset
        fields = [
            "id",
            "attraction",
            "type",
            "s3_key",
            "cdn_url",
            "is_featured",
            "caption",
            "attribution",
        ]
        read_only_fields = ["id"]


class DistrictSerializer(serializers.ModelSerializer):
    attraction_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = District
        fields = [
            "id",
            "name",
            "province",
            "description",
            "climate_zone",
            "peak_months",
            "lat",
            "lng",
            "attraction_count",
        ]
        read_only_fields = ["id", "attraction_count"]


class AttractionListSerializer(serializers.ModelSerializer):
    """Lean serializer used by the explorer grid (Prompt 5C)."""

    district_name = serializers.CharField(source="district.name", read_only=True)
    featured_media = serializers.SerializerMethodField()

    class Meta:
        model = Attraction
        fields = [
            "id",
            "name",
            "slug",
            "category",
            "district",
            "district_name",
            "crowd_index",
            "trend_score",
            "best_season",
            "featured_media",
        ]
        read_only_fields = fields

    def get_featured_media(self, obj: Attraction) -> dict | None:
        media = next(
            (m for m in obj.media.all() if m.is_featured), None
        )
        if media is None:
            return None
        return {
            "type": media.type,
            "url": media.cdn_url or media.s3_key,
            "caption": media.caption,
        }


class AttractionDetailSerializer(serializers.ModelSerializer):
    """Full payload for `/api/v1/attractions/<slug>/` (PRD §8.2)."""

    district = DistrictSerializer(read_only=True)
    media = MediaAssetSerializer(many=True, read_only=True)

    class Meta:
        model = Attraction
        fields = [
            "id",
            "name",
            "slug",
            "category",
            "description",
            "address",
            "lat",
            "lng",
            "entry_fee_lkr",
            "best_season",
            "crowd_index",
            "trend_score",
            "chroma_doc_id",
            "district",
            "media",
            "created_at",
        ]
        read_only_fields = fields
