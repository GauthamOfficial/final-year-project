"""
Sentiment / review persistence — direct port of PRD §7.1 `reviews` table.
"""

from __future__ import annotations

from django.db import models

from apps.attractions.models import Attraction


class ReviewSource(models.TextChoices):
    GOOGLE = "google", "Google"
    REDDIT = "reddit", "Reddit"
    TWITTER = "twitter", "Twitter / X"
    MANUAL = "manual", "Manual"


class SentimentLabel(models.TextChoices):
    POSITIVE = "positive", "Positive"
    NEUTRAL = "neutral", "Neutral"
    NEGATIVE = "negative", "Negative"


class Review(models.Model):
    attraction = models.ForeignKey(
        Attraction, on_delete=models.CASCADE, related_name="reviews"
    )
    source = models.CharField(max_length=10, choices=ReviewSource.choices)
    external_id = models.CharField(max_length=200, blank=True)
    body = models.TextField()
    sentiment_score = models.FloatField(null=True, blank=True)
    sentiment_label = models.CharField(
        max_length=10, choices=SentimentLabel.choices, blank=True
    )
    published_at = models.DateTimeField(null=True, blank=True)
    ingested_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "reviews"
        ordering = ["-ingested_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["source", "external_id"],
                name="uq_review_source_external_id",
                condition=~models.Q(external_id=""),
            )
        ]
        indexes = [
            models.Index(fields=["attraction", "-ingested_at"]),
            models.Index(fields=["sentiment_label"]),
        ]

    def __str__(self) -> str:
        return f"{self.source}:{self.attraction_id} {self.sentiment_label}"
