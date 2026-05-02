"""Serializers used by the admin dashboard endpoints."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.attractions.models import Attraction, District, MediaAsset
from apps.chat.models import ChatMessage, ChatSession
from apps.itinerary.models import Itinerary
from apps.sentiment.models import Review

User = get_user_model()


class AdminUserSerializer(serializers.ModelSerializer):
    chat_session_count = serializers.IntegerField(read_only=True, required=False)
    itinerary_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "role",
            "language",
            "home_country",
            "is_active",
            "is_staff",
            "is_superuser",
            "onboarding_complete",
            "created_at",
            "updated_at",
            "chat_session_count",
            "itinerary_count",
        ]
        read_only_fields = [
            "id",
            "email",
            "created_at",
            "updated_at",
            "is_superuser",
            "chat_session_count",
            "itinerary_count",
        ]


class AdminDistrictSerializer(serializers.ModelSerializer):
    attraction_count = serializers.IntegerField(read_only=True, required=False)

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


class AdminAttractionSerializer(serializers.ModelSerializer):
    district_name = serializers.CharField(source="district.name", read_only=True)
    media_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Attraction
        fields = [
            "id",
            "district",
            "district_name",
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
            "wikipedia_title",
            "youtube_video_id",
            "media_count",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "media_count", "district_name"]


class AdminMediaSerializer(serializers.ModelSerializer):
    attraction_name = serializers.CharField(
        source="attraction.name", read_only=True, default=""
    )
    district_name = serializers.CharField(
        source="district.name", read_only=True, default=""
    )

    class Meta:
        model = MediaAsset
        fields = [
            "id",
            "attraction",
            "attraction_name",
            "district",
            "district_name",
            "type",
            "s3_key",
            "cdn_url",
            "is_featured",
            "caption",
            "attribution",
            "license",
            "source_url",
        ]


class AdminItinerarySerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source="user.email", read_only=True)
    day_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Itinerary
        fields = [
            "id",
            "user",
            "user_email",
            "title",
            "start_date",
            "end_date",
            "budget_lkr",
            "group_size",
            "group_type",
            "status",
            "share_token",
            "created_at",
            "day_count",
        ]
        read_only_fields = fields


class AdminChatSessionSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source="user.email", read_only=True)
    message_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = ChatSession
        fields = [
            "id",
            "user",
            "user_email",
            "title",
            "language",
            "started_at",
            "last_activity_at",
            "message_count",
        ]
        read_only_fields = fields


class AdminChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = [
            "id",
            "session",
            "role",
            "content",
            "retrieved_docs",
            "tokens_used",
            "backend",
            "created_at",
        ]
        read_only_fields = fields


class AdminReviewSerializer(serializers.ModelSerializer):
    attraction_name = serializers.CharField(
        source="attraction.name", read_only=True
    )

    class Meta:
        model = Review
        fields = [
            "id",
            "attraction",
            "attraction_name",
            "source",
            "external_id",
            "body",
            "sentiment_score",
            "sentiment_label",
            "published_at",
            "ingested_at",
        ]
        read_only_fields = fields
