"""Tests for the PRD §10.3 trend score formula."""

from datetime import datetime, timedelta, timezone

from apps.sentiment.services import calculate_trend_score


def test_empty_yields_zero():
    assert calculate_trend_score([]) == 0.0


def test_recent_positive_reviews_score_high():
    now = datetime.now(timezone.utc)
    reviews = [
        {"sentiment_score": 0.95, "published_at": now - timedelta(hours=1)},
        {"sentiment_score": 0.87, "published_at": now - timedelta(hours=4)},
        {"sentiment_score": 0.91, "published_at": now - timedelta(hours=12)},
    ]
    score = calculate_trend_score(reviews)
    assert 6.0 <= score <= 10.0


def test_old_reviews_decay():
    now = datetime.now(timezone.utc)
    fresh = [{"sentiment_score": 1.0, "published_at": now}]
    stale = [{"sentiment_score": 1.0, "published_at": now - timedelta(days=20)}]
    assert calculate_trend_score(fresh) > calculate_trend_score(stale)


def test_volume_increases_score():
    now = datetime.now(timezone.utc)
    one = [{"sentiment_score": 0.5, "published_at": now}]
    many = [{"sentiment_score": 0.5, "published_at": now} for _ in range(40)]
    assert calculate_trend_score(many) > calculate_trend_score(one)
