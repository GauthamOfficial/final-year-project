"""
Project-level pytest fixtures.

`fake_chroma` provides an in-memory stand-in for ChromaDB that mirrors the
subset of the API surface RAGService consumes. This lets us exercise the
real RAGService logic without spinning up a Chroma persistent store.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest
from django.conf import settings


def pytest_configure(config):
    """Force local-memory cache for the test run so Redis isn't required."""
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "lankaguide-tests",
        }
    }


@dataclass
class FakeChromaCollection:
    """Tiny in-memory collection mimicking the chromadb Collection API."""

    ids: list[str] = field(default_factory=list)
    documents: list[str] = field(default_factory=list)
    metadatas: list[dict] = field(default_factory=list)

    def upsert(self, *, ids, documents, metadatas, embeddings=None):
        for cid, doc, meta in zip(ids, documents, metadatas):
            if cid in self.ids:
                idx = self.ids.index(cid)
                self.documents[idx] = doc
                self.metadatas[idx] = meta
            else:
                self.ids.append(cid)
                self.documents.append(doc)
                self.metadatas.append(meta)

    def query(self, *, query_embeddings, n_results=5, where=None):
        # Naive lexical scoring — sufficient for retrieval tests.
        n = min(n_results, len(self.ids))
        ids = self.ids[:n]
        docs = self.documents[:n]
        metas = self.metadatas[:n]
        # Cosine distance ∈ [0, 2]; pretend perfect match → 0.0
        distances = [0.1 * (i + 1) for i in range(n)]
        return {
            "ids": [ids],
            "documents": [docs],
            "metadatas": [metas],
            "distances": [distances],
        }


@pytest.fixture
def fake_chroma() -> FakeChromaCollection:
    coll = FakeChromaCollection()
    coll.upsert(
        ids=["doc-yala-1", "doc-sigiriya-1"],
        documents=[
            "Yala National Park is famous for the highest density of wild leopards "
            "anywhere on earth. Best visited February through July.",
            "Sigiriya is a 5th-century royal citadel; the dry season (May–September) "
            "offers the most reliable weather for the climb.",
        ],
        metadatas=[
            {"slug": "yala-national-park", "category": "wildlife", "attraction_id": 2, "district_id": 2},
            {"slug": "sigiriya", "category": "cultural", "attraction_id": 1, "district_id": 1},
        ],
    )
    return coll
