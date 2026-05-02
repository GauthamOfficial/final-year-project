"""Itinerary models — owned by an authenticated user."""

from __future__ import annotations

import secrets

from django.conf import settings
from django.db import models

from apps.attractions.models import Attraction, District


class GroupType(models.TextChoices):
    SOLO = "solo", "Solo"
    COUPLE = "couple", "Couple"
    FAMILY = "family", "Family"
    GROUP = "group", "Group"


class ItineraryStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    SAVED = "saved", "Saved"
    SHARED = "shared", "Shared"


def _new_share_token() -> str:
    return f"shr_{secrets.token_urlsafe(16)[:60]}"


class Itinerary(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="itineraries",
    )
    title = models.CharField(max_length=200, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    budget_lkr = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    group_size = models.PositiveSmallIntegerField(default=1)
    group_type = models.CharField(
        max_length=10, choices=GroupType.choices, default=GroupType.SOLO
    )
    status = models.CharField(
        max_length=10, choices=ItineraryStatus.choices, default=ItineraryStatus.DRAFT
    )
    share_token = models.CharField(
        max_length=64, unique=True, default=_new_share_token
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "itineraries"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title or f"Itinerary #{self.id}"


class ItineraryDay(models.Model):
    itinerary = models.ForeignKey(
        Itinerary, on_delete=models.CASCADE, related_name="days"
    )
    day_number = models.PositiveSmallIntegerField()
    district = models.ForeignKey(
        District, on_delete=models.SET_NULL, null=True, blank=True
    )
    notes = models.TextField(blank=True)
    ai_generated = models.BooleanField(default=True)

    class Meta:
        db_table = "itinerary_days"
        ordering = ["itinerary_id", "day_number"]
        unique_together = [("itinerary", "day_number")]

    def __str__(self) -> str:
        return f"{self.itinerary} · day {self.day_number}"


class ItineraryStop(models.Model):
    day = models.ForeignKey(
        ItineraryDay, on_delete=models.CASCADE, related_name="stops"
    )
    attraction = models.ForeignKey(Attraction, on_delete=models.CASCADE)
    stop_order = models.PositiveSmallIntegerField()
    arrival_time = models.TimeField(null=True, blank=True)
    duration_mins = models.PositiveSmallIntegerField(null=True, blank=True)
    tip = models.TextField(blank=True)

    class Meta:
        db_table = "itinerary_stops"
        ordering = ["day_id", "stop_order"]

    def __str__(self) -> str:
        return f"{self.day} · stop {self.stop_order}: {self.attraction.name}"
