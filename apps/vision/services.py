"""
VisionService — Prompt 4C (PRD §4.1.4 / §5.3 / §8.3).

Pipeline:

    image_file → preprocess(224×224, ImageNet normalisation)
              → MobileNetV2 backbone (ImageNet weights from torchvision)
              → placeholder linear head (50 Sri Lanka landmark classes)
              → top-3 (label, confidence)
              → if top1.confidence > VISION_CONFIDENCE_THRESHOLD:
                    RAGService.query(landmark_name) → ai_summary

Honesty notes:
  * The classifier head is a deterministic projection seeded from the model
    weights. It is *not* a fine-tuned Sri-Lanka classifier — that is a Phase-4
    deliverable per PRD §12.1. The placeholder gives stable predictions on
    identical inputs so the API contract holds and the UI can be exercised.
  * Swapping in a real fine-tuned head later is a one-method change:
    `_LandmarkHead.predict()`.
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from typing import Any, BinaryIO

from django.conf import settings
from django.db.models import Q

from apps.attractions.models import Attraction

logger = logging.getLogger("lankaguide.vision")

VISION_CONFIDENCE_THRESHOLD = 0.70  # PRD §4.1.4 / §5.3
INPUT_SIZE = 224
TOP_K = 3
NUM_PLACEHOLDER_CLASSES = 50


@dataclass
class Prediction:
    label: str
    slug: str
    attraction_id: int | None
    confidence: float


# ───────────────────────── Backbone (lazy) ─────────────────────────────
_BACKBONE = None
_TRANSFORM = None


def _get_backbone():
    """Load torchvision MobileNetV2 once per process."""
    global _BACKBONE, _TRANSFORM
    if _BACKBONE is not None:
        return _BACKBONE, _TRANSFORM

    import torch
    from torchvision import models, transforms

    weights = models.MobileNet_V2_Weights.DEFAULT
    backbone = models.mobilenet_v2(weights=weights)
    backbone.eval()
    # Strip the ImageNet classification head — we want pooled features (1280-d).
    backbone.classifier = torch.nn.Identity()

    _BACKBONE = backbone
    _TRANSFORM = transforms.Compose(
        [
            transforms.Resize(256),
            transforms.CenterCrop(INPUT_SIZE),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
            ),
        ]
    )
    return _BACKBONE, _TRANSFORM


# ───────────────────────── Placeholder head ────────────────────────────
class _LandmarkHead:
    """
    50-class deterministic projection. Treats the MobileNet feature vector
    as a query and dot-products it against a fixed orthonormal basis seeded
    by class index — gives stable, reproducible "predictions" without
    requiring training data.

    Replace `predict()` with a real torch.nn.Linear(1280, N) once the
    fine-tuned weights arrive.
    """

    def __init__(self, classes: list[Attraction]):
        self.classes = classes[:NUM_PLACEHOLDER_CLASSES] or []

    def predict(self, feature_vector) -> list[tuple[Attraction, float]]:
        import torch

        if not self.classes:
            return []
        feat = feature_vector.flatten()
        scores: list[float] = []
        # Deterministic per-class basis: torch.manual_seed(id) -> random vector.
        for klass in self.classes:
            generator = torch.Generator().manual_seed(int(klass.id))
            basis = torch.randn(feat.shape[0], generator=generator)
            basis = basis / basis.norm()
            scores.append(float((feat / (feat.norm() + 1e-8)) @ basis))
        # Softmax for confidence-like outputs.
        scores_t = torch.tensor(scores)
        probs = torch.softmax(scores_t * 8.0, dim=0).tolist()
        ranked = sorted(zip(self.classes, probs), key=lambda x: x[1], reverse=True)
        return ranked


# ───────────────────────── Service ─────────────────────────────────────
class VisionService:
    def __init__(self, head: _LandmarkHead | None = None):
        self._head: _LandmarkHead | None = head

    def _load_head(self) -> _LandmarkHead:
        if self._head is not None:
            return self._head
        # Pull a stable set of attractions to act as the placeholder classes.
        candidates = list(
            Attraction.objects.filter(
                Q(category__in=["cultural", "religious", "wildlife", "adventure"])
            )
            .order_by("-trend_score")[:NUM_PLACEHOLDER_CLASSES]
        )
        self._head = _LandmarkHead(candidates)
        return self._head

    def identify(self, image_file: BinaryIO | bytes | str) -> dict:
        """
        Args:
            image_file: a file-like, raw bytes, or a path to an image.

        Returns:
            {
              "predictions": [{label, slug, attraction_id, confidence}],
              "top_match": str | None,
              "attraction_slug": str | None,
              "ai_summary": str | None,
              "backend": str,
            }
        """
        image = self._open_image(image_file)
        backbone, transform = _get_backbone()

        import torch

        with torch.no_grad():
            tensor = transform(image).unsqueeze(0)  # [1,3,224,224]
            features = backbone(tensor)  # [1, 1280]

        head = self._load_head()
        ranked = head.predict(features[0])
        top = ranked[:TOP_K]

        predictions = [
            Prediction(
                label=att.name,
                slug=att.slug,
                attraction_id=att.id,
                confidence=round(float(score), 4),
            )
            for att, score in top
        ]

        top_match: Prediction | None = predictions[0] if predictions else None
        ai_summary: str | None = None
        if (
            top_match is not None
            and top_match.confidence >= VISION_CONFIDENCE_THRESHOLD
        ):
            ai_summary = self._summarise(top_match.label)

        return {
            "predictions": [p.__dict__ for p in predictions],
            "top_match": top_match.label if top_match else None,
            "attraction_slug": top_match.slug if top_match else None,
            "ai_summary": ai_summary,
            "backend": (
                "mobilenet_v2-imagenet+placeholder-head"
                if not settings.GEMINI_API_KEY
                else "mobilenet_v2-imagenet+placeholder-head+gemini"
            ),
        }

    # ─────────────────── Helpers ───────────────────────────────────────
    @staticmethod
    def _open_image(image_file: BinaryIO | bytes | str):
        from PIL import Image

        if isinstance(image_file, (bytes, bytearray)):
            buf = io.BytesIO(image_file)
            return Image.open(buf).convert("RGB")
        if isinstance(image_file, str):
            return Image.open(image_file).convert("RGB")
        # Django InMemoryUploadedFile / file-like
        return Image.open(image_file).convert("RGB")

    @staticmethod
    def _summarise(landmark: str) -> str | None:
        """RAG-grounded summary; falls back to a templated string offline."""
        try:
            from apps.chat.services import RAGService

            rag = RAGService()
            result = rag.query(
                user_message=(
                    f"Tell me about {landmark} in Sri Lanka — its history, "
                    "what to expect on a visit, and best time to go."
                ),
                language="en",
            )
            return result.get("response")
        except Exception as exc:  # noqa: BLE001
            logger.warning("VisionService summary fell back: %s", exc)
            return f"{landmark} is a notable attraction in Sri Lanka."
