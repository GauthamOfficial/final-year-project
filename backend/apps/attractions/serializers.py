"""DRF serializers for the `attractions` app (PRD §8.2)."""

from __future__ import annotations

from rest_framework import serializers

from .models import Attraction, District, MediaAsset, SeasonalData
from .seasonal_utils import best_month_names


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
            "slug",
            "province",
            "description",
            "climate_zone",
            "peak_months",
            "lat",
            "lng",
            "youtube_video_ids",
            "hero_image_url",
            "attraction_count",
        ]
        read_only_fields = ["id", "attraction_count"]


class SeasonalDataSerializer(serializers.ModelSerializer):
    month_name = serializers.SerializerMethodField()

    class Meta:
        model = SeasonalData
        fields = [
            "month",
            "month_name",
            "crowd_index",
            "weather_rating",
            "is_peak_season",
            "visitor_note",
        ]

    def get_month_name(self, obj: SeasonalData) -> str:
        return SeasonalData.MONTH_NAMES[obj.month - 1]


class AttractionListSerializer(serializers.ModelSerializer):
    """Lean serializer used by the explorer grid (Prompt 5C)."""

    district_name = serializers.CharField(source="district.name", read_only=True)
    featured_media = serializers.SerializerMethodField()
    best_months_names = serializers.SerializerMethodField()

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
            "sentiment_label",
            "sentiment_score",
            "positive_pct",
            "sentiment_summary",
            "best_months_names",
        ]
        read_only_fields = fields

    def get_best_months_names(self, obj: Attraction) -> list[str]:
        rows = list(obj.seasonal_data.all())
        if not rows:
            return []
        return best_month_names(sorted(rows, key=lambda r: r.month))

    def get_featured_media(self, obj: Attraction) -> dict | None:
        media_list = list(obj.media.all())
        media = next((m for m in media_list if m.is_featured), None)
        if media is None and media_list:
            media = media_list[0]
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
    media = serializers.SerializerMethodField()
    best_months_names = serializers.SerializerMethodField()

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
            "sentiment_label",
            "sentiment_score",
            "positive_pct",
            "sentiment_summary",
            "chroma_doc_id",
            "district",
            "media",
            "created_at",
            "best_months_names",
        ]
        read_only_fields = fields

    def get_best_months_names(self, obj: Attraction) -> list[str]:
        rows = list(obj.seasonal_data.all())
        if not rows:
            return []
        return best_month_names(sorted(rows, key=lambda r: r.month))

    def get_media(self, obj: Attraction):
        """
        Return only media that appears relevant to this attraction.
        This guards against noisy Wikimedia gallery pulls that can include
        nearby-but-different landmarks.
        """
        media_list = list(obj.media.all())
        if not media_list:
            return []

        def _tokens(text: str) -> set[str]:
            stop = {
                "the",
                "and",
                "with",
                "from",
                "near",
                "fort",
                "beach",
                "temple",
                "museum",
                "park",
                "lake",
                "river",
                "old",
                "new",
                "sri",
                "lanka",
                "city",
            }
            cleaned = "".join(ch.lower() if ch.isalnum() else " " for ch in (text or ""))
            return {
                token
                for token in cleaned.split()
                if len(token) >= 4 and token not in stop
            }

        def _has_non_photo_keywords(text: str) -> bool:
            bad = {
                "map",
                "maps",
                "plan",
                "layout",
                "diagram",
                "sketch",
                "drawing",
                "locator",
                "topographic",
                "topography",
            }
            text_tokens = _tokens(text)
            return bool(text_tokens.intersection(bad))

        attraction_tokens = _tokens(obj.name) | _tokens(obj.wikipedia_title or "")
        if not attraction_tokens:
            return MediaAssetSerializer(media_list, many=True).data

        filtered: list[MediaAsset] = []
        for media in media_list:
            haystack = " ".join(
                [
                    media.caption or "",
                    media.source_url or "",
                ]
            )
            if _has_non_photo_keywords(haystack):
                continue
            haystack_tokens = _tokens(haystack)
            if attraction_tokens.intersection(haystack_tokens):
                filtered.append(media)

        # Keep at least the featured image when metadata is sparse.
        if not filtered:
            featured = next((m for m in media_list if m.is_featured), None)
            filtered = [featured] if featured else media_list[:1]

        return MediaAssetSerializer(filtered, many=True).data
