"""
`python manage.py start_sentiment_worker` — Prompt 6B.

Long-running Kafka consumer:
  - Reads raw review payloads from `raw_reviews`.
  - Runs the RoBERTa classifier (lazy load).
  - Persists Review row in MySQL with sentiment_score + sentiment_label.
  - Emits a slim payload to `sentiment_done` for the trend aggregator.

Expected message shape on `raw_reviews`:
{
  "attraction_id": int,
  "source": "google" | "reddit" | "twitter" | "manual",
  "external_id": "abc123",      // optional, used for dedupe
  "body": "Tourists love the sunrise hike...",
  "published_at": "2025-04-12T08:21:00Z"  // optional ISO 8601
}
"""

from __future__ import annotations

import logging
import time
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.sentiment.kafka_io import make_consumer, make_producer, safe_send
from apps.sentiment.models import Review, ReviewSource
from apps.sentiment.services import classify

logger = logging.getLogger("lankaguide.sentiment.worker")


class Command(BaseCommand):
    help = "Consume raw_reviews from Kafka, classify sentiment, persist."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true",
                            help="Process one batch then exit (handy for tests/cron).")

    def handle(self, *args, **opts):
        consumer = make_consumer(
            settings.KAFKA_TOPIC_RAW_REVIEWS, group_id="sentiment_worker"
        )
        producer = make_producer()
        self.stdout.write(self.style.SUCCESS(
            f"Connected to Kafka @ {settings.KAFKA_BOOTSTRAP_SERVERS} — "
            f"consuming '{settings.KAFKA_TOPIC_RAW_REVIEWS}'"
        ))

        try:
            while True:
                processed = 0
                for msg in consumer:
                    self._process_message(msg.value, producer)
                    processed += 1
                if opts["once"]:
                    break
                if processed == 0:
                    time.sleep(2.0)
        except KeyboardInterrupt:
            self.stdout.write("Shutting down sentiment worker.")
        finally:
            try:
                consumer.close()
                producer.close()
            except Exception:  # noqa: BLE001
                pass

    @staticmethod
    def _process_message(payload: dict, producer) -> None:
        attraction_id = payload.get("attraction_id")
        body = payload.get("body", "").strip()
        if not attraction_id or not body:
            logger.warning("Skipping malformed review: %s", payload)
            return
        result = classify(body)

        published_at = payload.get("published_at")
        if isinstance(published_at, str):
            try:
                published_at = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            except ValueError:
                published_at = None

        review, created = Review.objects.update_or_create(
            source=payload.get("source", ReviewSource.MANUAL),
            external_id=payload.get("external_id", "") or "",
            defaults={
                "attraction_id": attraction_id,
                "body": body,
                "sentiment_score": result.score,
                "sentiment_label": result.label,
                "published_at": published_at,
            },
        )
        logger.info(
            "Review #%s %s — %s (%.3f)",
            review.id,
            "stored" if created else "updated",
            result.label,
            result.score,
        )
        safe_send(
            producer,
            settings.KAFKA_TOPIC_SENTIMENT_DONE,
            {
                "review_id": review.id,
                "attraction_id": attraction_id,
                "sentiment_score": result.score,
                "sentiment_label": result.label,
            },
        )
