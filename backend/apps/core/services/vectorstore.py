"""
Thin wrapper around ChromaDB (PRD §6, §9.1.2).

Provides two client builders:
- `get_collection()` returns a persistent ChromaDB collection.
- `get_chroma_client()` returns the underlying client for advanced ops.

Imports are intentionally lazy so unrelated tests don't load ChromaDB.
"""

from __future__ import annotations

import logging
from pathlib import Path

from django.conf import settings

logger = logging.getLogger("lankaguide.core.vectorstore")


def get_chroma_client():
    import chromadb

    persist_dir = Path(settings.CHROMA_PERSIST_DIR)
    persist_dir.mkdir(parents=True, exist_ok=True)
    logger.debug("Opening ChromaDB at %s", persist_dir)
    return chromadb.PersistentClient(path=str(persist_dir))


def get_collection(name: str | None = None):
    name = name or settings.CHROMA_COLLECTION
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )
