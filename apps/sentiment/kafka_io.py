"""
Thin wrappers around `kafka-python` so the Django commands stay testable.

Usage:

    consumer = make_consumer(settings.KAFKA_TOPIC_RAW_REVIEWS, group_id="sentiment_worker")
    for msg in consumer:
        ...

    producer = make_producer()
    producer.send(topic, {"attraction_id": 1, ...})
"""

from __future__ import annotations

import json
import logging
from typing import Any

from django.conf import settings

logger = logging.getLogger("lankaguide.sentiment.kafka")


def make_consumer(topic: str, *, group_id: str):
    from kafka import KafkaConsumer  # local import; optional dep at runtime

    return KafkaConsumer(
        topic,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id=group_id,
        enable_auto_commit=True,
        auto_offset_reset="earliest",
        value_deserializer=lambda b: json.loads(b.decode("utf-8")),
        consumer_timeout_ms=10_000,
    )


def make_producer():
    from kafka import KafkaProducer

    return KafkaProducer(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
        acks="all",
    )


def safe_send(producer, topic: str, payload: dict[str, Any]) -> None:
    """Fire-and-forget send with graceful degradation when Kafka is down."""
    try:
        producer.send(topic, payload)
        producer.flush(timeout=5)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Kafka send to '%s' failed (%s) — payload dropped.", topic, exc)
