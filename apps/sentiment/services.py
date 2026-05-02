"""
Trend-score calculation + sentiment classifier wrapper.

The classifier is the Hugging Face model named in PRD §4.2.1
(`cardiffnlp/twitter-roberta-base-sentiment`). Loading is lazy and the
weights are downloaded on first use; offline runs fall back to a
deterministic VADER-style rule-based classifier so the whole pipeline is
exercisable without network access (PRD §14.1 — EC2 OOM mitigation).
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from datetime import datetime, timezone

from .models import SentimentLabel

logger = logging.getLogger("lankaguide.sentiment")

MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment"


# ───────────────────────── Trend Score (PRD §10.3) ────────────────────
def calculate_trend_score(recent_reviews: list[dict]) -> float:
    """
    recent_reviews: dicts with keys {sentiment_score: float (-1..1),
                                     published_at: datetime}
    Returns: trend_score in [0.0, 10.0].
    """
    if not recent_reviews:
        return 0.0

    now = datetime.now(timezone.utc)
    weighted: list[float] = []
    for r in recent_reviews:
        published_at = r.get("published_at") or now
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        age_hours = max(0.0, (now - published_at).total_seconds() / 3600.0)
        decay = math.exp(-0.01 * age_hours)
        weighted.append((r.get("sentiment_score") or 0.0) * decay)

    avg_sentiment = sum(weighted) / len(weighted)
    volume_bonus = min(len(recent_reviews) / 50.0, 1.0)
    raw = (avg_sentiment + 1) / 2
    return round((raw * 0.7 + volume_bonus * 0.3) * 10, 2)


# ───────────────────────── Classifier ─────────────────────────────────
@dataclass
class SentimentResult:
    label: str  # SentimentLabel
    score: float  # -1.0 .. 1.0


_PIPELINE = None


def _load_pipeline():
    global _PIPELINE
    if _PIPELINE is not None:
        return _PIPELINE
    try:
        from transformers import pipeline

        _PIPELINE = pipeline(
            "sentiment-analysis",
            model=MODEL_NAME,
            tokenizer=MODEL_NAME,
            device=-1,  # CPU only — PRD §13
        )
        logger.info("Loaded HF sentiment model: %s", MODEL_NAME)
    except Exception as exc:  # noqa: BLE001
        logger.warning("HF sentiment model unavailable (%s); using rule-based fallback.", exc)
        _PIPELINE = "fallback"
    return _PIPELINE


_POS_WORDS = {
    "love", "amazing", "great", "wonderful", "stunning", "beautiful",
    "fantastic", "excellent", "best", "loved", "perfect", "awesome",
    "incredible", "spectacular", "must-see", "magical",
}
_NEG_WORDS = {
    "bad", "worst", "terrible", "awful", "disappointing", "rude",
    "dirty", "scam", "overpriced", "boring", "crowded", "hate",
    "avoid", "skip", "horrible",
}


def _rule_based(text: str) -> SentimentResult:
    tokens = {t.strip(".,!?;:\"'()").lower() for t in text.split()}
    pos = len(tokens & _POS_WORDS)
    neg = len(tokens & _NEG_WORDS)
    if pos == 0 and neg == 0:
        return SentimentResult(SentimentLabel.NEUTRAL, 0.0)
    score = (pos - neg) / max(pos + neg, 1)
    if score > 0.15:
        return SentimentResult(SentimentLabel.POSITIVE, round(score, 3))
    if score < -0.15:
        return SentimentResult(SentimentLabel.NEGATIVE, round(score, 3))
    return SentimentResult(SentimentLabel.NEUTRAL, round(score, 3))


def classify(text: str) -> SentimentResult:
    text = (text or "").strip()
    if not text:
        return SentimentResult(SentimentLabel.NEUTRAL, 0.0)

    pipe = _load_pipeline()
    if pipe == "fallback":
        return _rule_based(text)

    try:
        out = pipe(text[:512])[0]
        label = out["label"].upper()
        score_raw = float(out["score"])
        # cardiffnlp labels: LABEL_0=neg, LABEL_1=neu, LABEL_2=pos
        mapping = {
            "LABEL_0": (SentimentLabel.NEGATIVE, -1.0),
            "LABEL_1": (SentimentLabel.NEUTRAL, 0.0),
            "LABEL_2": (SentimentLabel.POSITIVE, 1.0),
            "POSITIVE": (SentimentLabel.POSITIVE, 1.0),
            "NEUTRAL": (SentimentLabel.NEUTRAL, 0.0),
            "NEGATIVE": (SentimentLabel.NEGATIVE, -1.0),
        }
        sentiment_label, sign = mapping.get(label, (SentimentLabel.NEUTRAL, 0.0))
        return SentimentResult(sentiment_label, round(sign * score_raw, 4))
    except Exception as exc:  # noqa: BLE001
        logger.warning("HF classifier crashed: %s — falling back.", exc)
        return _rule_based(text)
