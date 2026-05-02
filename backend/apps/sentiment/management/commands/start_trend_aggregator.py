"""
`python manage.py start_trend_aggregator` — Prompt 6B (companion to the
sentiment worker).

Consumes `sentiment_done`, recomputes each affected attraction's
`trend_score` over the last 7 days using the formula from PRD §10.3,
and updates `attractions.trend_score`. Also invalidates the trend cache
key so the next `/api/v1/trends/attractions/` request recomputes.
"""

from __future__ import annotations

import logging
import time
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.attractions.models import Attraction
from apps.sentiment.kafka_io import make_consumer
from apps.sentiment.models import Review
from apps.sentiment.services import calculate_trend_score

logger = logging.getLogger("lankaguide.sentiment.aggregator")

LOOKBACK_DAYS = 7
TREND_CACHE_KEY = "trends:attractions:top"


class Command(BaseCommand):
    help = "Recompute trend scores from sentiment_done events."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true")
        parser.add_argument(
            "--recompute-all",
            action="store_true",
            help="Recompute trend_score for every attraction immediately and exit.",
        )

    def handle(self, *args, **opts):
        if opts["recompute_all"]:
            self._recompute_all()
            return

        consumer = make_consumer(
            settings.KAFKA_TOPIC_SENTIMENT_DONE, group_id="trend_aggregator"
        )
        self.stdout.write(self.style.SUCCESS(
            f"Aggregator listening on '{settings.KAFKA_TOPIC_SENTIMENT_DONE}'"
        ))
        try:
            while True:
                processed = 0
                for msg in consumer:
                    attraction_id = msg.value.get("attraction_id")
                    if attraction_id:
                        self._recompute_attraction(attraction_id)
                        processed += 1
                if opts["once"]:
                    break
                if processed == 0:
                    time.sleep(5.0)
        except KeyboardInterrupt:
            self.stdout.write("Shutting down trend aggregator.")
        finally:
            try:
                consumer.close()
            except Exception:  # noqa: BLE001
                pass

    def _recompute_attraction(self, attraction_id: int) -> None:
        cutoff = timezone.now() - timedelta(days=LOOKBACK_DAYS)
        recent = list(
            Review.objects.filter(
                attraction_id=attraction_id, ingested_at__gte=cutoff
            ).values("sentiment_score", "published_at", "ingested_at")
        )
        for r in recent:
            r["published_at"] = r.get("published_at") or r["ingested_at"]

        score = calculate_trend_score(recent)
        Attraction.objects.filter(id=attraction_id).update(trend_score=score)
        cache.delete(TREND_CACHE_KEY)
        logger.info("Recomputed trend for attraction %s = %.2f", attraction_id, score)

    def _recompute_all(self) -> None:
        attraction_ids = Review.objects.values_list("attraction_id", flat=True).distinct()
        for aid in attraction_ids:
            self._recompute_attraction(aid)
        self.stdout.write(self.style.SUCCESS(
            f"Recomputed trends for {len(set(attraction_ids))} attractions."
        ))
