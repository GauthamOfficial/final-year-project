"""Serializers for the itinerary endpoints (PRD §8.3)."""

from __future__ import annotations

from rest_framework import serializers

from apps.attractions.models import AttractionCategory

from .models import GroupType, Itinerary, ItineraryDay, ItineraryStop


class GenerateItineraryRequestSerializer(serializers.Serializer):
    """Body schema for `POST /api/v1/itinerary/generate/` (PRD §8.3)."""

    start_date = serializers.DateField()
    end_date = serializers.DateField()
    budget_lkr = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=0
    )
    interests = serializers.ListField(
        child=serializers.ChoiceField(choices=AttractionCategory.choices),
        allow_empty=False,
    )
    district_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1), allow_empty=False
    )
    group_type = serializers.ChoiceField(
        choices=GroupType.choices, default=GroupType.SOLO
    )
    group_size = serializers.IntegerField(min_value=1, default=1)
    title = serializers.CharField(max_length=200, required=False, allow_blank=True)

    def validate(self, attrs: dict) -> dict:
        if attrs["end_date"] < attrs["start_date"]:
            raise serializers.ValidationError(
                {"end_date": "end_date must be on or after start_date."}
            )
        days = (attrs["end_date"] - attrs["start_date"]).days + 1
        if days > 30:
            raise serializers.ValidationError("Itineraries are capped at 30 days.")
        attrs["num_days"] = days
        return attrs


class ItineraryStopSerializer(serializers.ModelSerializer):
    attraction_id = serializers.IntegerField(source="attraction.id", read_only=True)
    name = serializers.CharField(source="attraction.name", read_only=True)
    slug = serializers.CharField(source="attraction.slug", read_only=True)

    class Meta:
        model = ItineraryStop
        fields = [
            "id",
            "stop_order",
            "attraction_id",
            "name",
            "slug",
            "arrival_time",
            "duration_mins",
            "tip",
        ]


class ItineraryDaySerializer(serializers.ModelSerializer):
    district_name = serializers.CharField(source="district.name", read_only=True)
    stops = ItineraryStopSerializer(many=True, read_only=True)

    class Meta:
        model = ItineraryDay
        fields = [
            "id",
            "day_number",
            "district",
            "district_name",
            "notes",
            "ai_generated",
            "stops",
        ]


class ItinerarySerializer(serializers.ModelSerializer):
    days = ItineraryDaySerializer(many=True, read_only=True)

    class Meta:
        model = Itinerary
        fields = [
            "id",
            "title",
            "start_date",
            "end_date",
            "budget_lkr",
            "group_size",
            "group_type",
            "status",
            "share_token",
            "created_at",
            "days",
        ]
        read_only_fields = ["id", "share_token", "created_at", "days"]
