"""
Models for the `attractions` app.

Direct mapping of the MySQL DDL in PRD §7.1 (`districts`, `attractions`,
`media_assets`). Field types and constraints follow the schema as closely as
Django's ORM allows; deviations are documented inline.
"""

from __future__ import annotations

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


# ───────────────────────── Choice Enums ─────────────────────────────────
class ClimateZone(models.TextChoices):
    WET = "wet", "Wet"
    DRY = "dry", "Dry"
    INTERMEDIATE = "intermediate", "Intermediate"


class AttractionCategory(models.TextChoices):
    BEACH = "beach", "Beach"
    WILDLIFE = "wildlife", "Wildlife"
    CULTURAL = "cultural", "Cultural"
    RELIGIOUS = "religious", "Religious"
    ADVENTURE = "adventure", "Adventure"
    FOOD = "food", "Food"


class MediaType(models.TextChoices):
    IMAGE = "image", "Image"
    VIDEO = "video", "Video"


# ───────────────────────── Districts ────────────────────────────────────
class District(models.Model):
    """One of Sri Lanka's 25 administrative districts."""

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, blank=True, db_index=True)
    province = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    climate_zone = models.CharField(
        max_length=16, choices=ClimateZone.choices, default=ClimateZone.WET
    )
    # JSON array of month numbers (1-12) considered "peak" for tourism.
    peak_months = models.JSONField(default=list, blank=True)
    lat = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    lng = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    # Curated YouTube video IDs (just the v= part) showcased on /gallery/<district>.
    youtube_video_ids = models.JSONField(default=list, blank=True)
    # Optional hero image URL (Wikimedia Commons file or local /media path).
    hero_image_url = models.URLField(blank=True, max_length=600)

    class Meta:
        db_table = "districts"
        ordering = ["name"]
        indexes = [models.Index(fields=["province"])]

    def __str__(self) -> str:
        return f"{self.name} ({self.province})"


# ───────────────────────── Attractions ──────────────────────────────────
class Attraction(models.Model):
    """A point of interest (temple, beach, park, …) within a district."""

    district = models.ForeignKey(
        District, on_delete=models.CASCADE, related_name="attractions"
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    category = models.CharField(
        max_length=16, choices=AttractionCategory.choices
    )
    description = models.TextField(blank=True)
    address = models.CharField(max_length=300, blank=True)
    lat = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    lng = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    entry_fee_lkr = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    # JSON array of month numbers (1-12) when the attraction is at its best.
    best_season = models.JSONField(default=list, blank=True)
    crowd_index = models.PositiveSmallIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Steady-state crowd level (1 quiet → 10 packed).",
    )
    trend_score = models.FloatField(default=0.0)
    chroma_doc_id = models.CharField(max_length=128, blank=True)
    wikipedia_title = models.CharField(max_length=200, blank=True)
    youtube_video_id = models.CharField(max_length=32, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "attractions"
        ordering = ["-trend_score", "name"]
        indexes = [
            models.Index(fields=["category"]),
            models.Index(fields=["district"]),
            models.Index(fields=["-trend_score"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} — {self.district.name}"


# ───────────────────────── Media Assets ─────────────────────────────────
class MediaAsset(models.Model):
    """Image or video asset associated with an attraction or district."""

    attraction = models.ForeignKey(
        Attraction,
        on_delete=models.CASCADE,
        related_name="media",
        null=True,
        blank=True,
    )
    district = models.ForeignKey(
        District,
        on_delete=models.CASCADE,
        related_name="media",
        null=True,
        blank=True,
    )
    type = models.CharField(max_length=8, choices=MediaType.choices)
    s3_key = models.CharField(max_length=600)
    cdn_url = models.CharField(max_length=600, blank=True)
    is_featured = models.BooleanField(default=False)
    caption = models.TextField(blank=True)
    attribution = models.CharField(max_length=300, blank=True)
    license = models.CharField(max_length=120, blank=True)
    source_url = models.URLField(max_length=600, blank=True)

    class Meta:
        db_table = "media_assets"
        ordering = ["-is_featured", "id"]

    def __str__(self) -> str:
        target = (
            self.attraction.name
            if self.attraction
            else (self.district.name if self.district else "global")
        )
        return f"{self.type}: {target}"
