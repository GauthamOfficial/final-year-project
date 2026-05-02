"""
Pytest coverage for `RAGService` (Prompt 6A — PRD Appendix).

We use the deterministic `HashEmbeddingClient` for embeddings (no Gemini
needed) and the `fake_chroma` fixture for the vector store, so the tests
exercise the real prompt-assembly + caching code paths.
"""

from __future__ import annotations

import pytest
from django.core.cache import cache

from apps.chat.services import RAGService
from apps.core.services.embeddings import HashEmbeddingClient


pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


def test_query_returns_response_and_sources(fake_chroma):
    rag = RAGService(
        embed_client=HashEmbeddingClient(),
        gemini_client=None,
        collection=fake_chroma,
    )
    result = rag.query("Where can I see leopards in Sri Lanka?")
    assert "response" in result
    assert isinstance(result["response"], str) and result["response"]
    assert "sources" in result
    assert len(result["sources"]) > 0
    # Each source has the documented shape (PRD §8.3).
    for src in result["sources"]:
        assert "doc_id" in src
        assert "title" in src
        assert "relevance" in src
    assert result["cached"] is False
    assert result["backend"] == "extractive-offline"


def test_query_is_cached_on_repeat(fake_chroma, mocker):
    rag = RAGService(
        embed_client=HashEmbeddingClient(),
        gemini_client=None,
        collection=fake_chroma,
    )
    spy = mocker.spy(fake_chroma, "query")

    first = rag.query("What's the best time to visit Sigiriya?")
    second = rag.query("What's the best time to visit Sigiriya?")

    assert first["response"] == second["response"]
    assert first["cached"] is False
    assert second["cached"] is True
    # ChromaDB queried only once — the second call was served from Redis.
    assert spy.call_count == 1


def test_query_handles_chroma_failure_gracefully(mocker):
    class ExplodingCollection:
        def query(self, **kwargs):
            raise RuntimeError("boom")

    rag = RAGService(
        embed_client=HashEmbeddingClient(),
        gemini_client=None,
        collection=ExplodingCollection(),
    )
    result = rag.query("Anything")
    assert "response" in result
    assert result["sources"] == []
    # The fallback message should mention there's no info.
    assert "do not yet" in result["response"].lower() or "no curated" in result["response"].lower()


def test_query_with_gemini_client_uses_response(fake_chroma, mocker):
    """When a Gemini client is injected we surface its `text` output."""

    class FakeUsage:
        total_token_count = 312

    class FakeResponse:
        text = "AI-grounded answer about Sigiriya."
        usage_metadata = FakeUsage()

    fake_gemini = mocker.MagicMock()
    fake_gemini.generate_content.return_value = FakeResponse()

    rag = RAGService(
        embed_client=HashEmbeddingClient(),
        gemini_client=fake_gemini,
        collection=fake_chroma,
    )
    result = rag.query("Plan a Sigiriya visit")

    assert result["response"] == "AI-grounded answer about Sigiriya."
    assert result["tokens_used"] == 312
    fake_gemini.generate_content.assert_called_once()
    call_args = fake_gemini.generate_content.call_args
    prompt = call_args.args[0]
    # Prompt structure (PRD §9.3) — system + retrieval block + user query.
    assert "LankaGuide AI" in prompt
    assert "RETRIEVED KNOWLEDGE" in prompt
    assert "Plan a Sigiriya visit" in prompt
