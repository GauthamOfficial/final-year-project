"""
Pytest coverage for `RAGService`.

Tests inject a fake Gemini client + a fake Chroma collection so we exercise
the real prompt-assembly + caching code paths without making network calls.
"""

from __future__ import annotations

import pytest
from django.core.cache import cache

from apps.chat.services import (
    RAGService,
    _itinerary_response_is_duplicate,
)
from apps.core.services.embeddings import HashEmbeddingClient


pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def gemini_settings(settings):
    settings.GEMINI_API_KEY = "test-key"
    return settings


def _make_rag(*, gemini, collection):
    return RAGService(
        embed_client=HashEmbeddingClient(),
        gemini_client=gemini,
        collection=collection,
    )


def test_init_without_api_key_raises(settings):
    settings.GEMINI_API_KEY = ""
    with pytest.raises(RuntimeError):
        RAGService(
            embed_client=HashEmbeddingClient(),
            gemini_client=object(),
            collection=None,
        )


def test_query_returns_grounded_gemini_response(fake_chroma, mocker, gemini_settings):
    class FakeUsage:
        total_token_count = 312

    class FakeResponse:
        text = "Yala has the highest density of leopards in the world."
        usage_metadata = FakeUsage()

    fake_gemini = mocker.MagicMock()
    fake_gemini.generate_content.return_value = FakeResponse()

    rag = _make_rag(gemini=fake_gemini, collection=fake_chroma)
    result = rag.query("Where can I see leopards in Sri Lanka?")

    assert "leopards" in result["response"].lower()
    assert result["tokens_used"] == 312
    assert len(result["sources"]) > 0
    assert result["backend"] == "gemini"
    fake_gemini.generate_content.assert_called()


def test_query_returns_honest_no_info_when_no_chunks(mocker, gemini_settings):
    class EmptyCollection:
        def query(self, **kwargs):
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

    fake_gemini = mocker.MagicMock()
    rag = _make_rag(gemini=fake_gemini, collection=EmptyCollection())

    result = rag.query("Tell me about something obscure")
    assert result["sources"] == []
    assert "don't have" in result["response"].lower() or "no curated" in result["response"].lower()
    fake_gemini.generate_content.assert_not_called()


def test_query_handles_chroma_failure_gracefully(mocker, gemini_settings):
    class ExplodingCollection:
        def query(self, **kwargs):
            raise RuntimeError("boom")

    fake_gemini = mocker.MagicMock()
    rag = _make_rag(gemini=fake_gemini, collection=ExplodingCollection())

    result = rag.query("Anything")
    assert result["sources"] == []
    fake_gemini.generate_content.assert_not_called()


def test_query_is_cached_on_repeat(fake_chroma, mocker, gemini_settings):
    class FakeUsage:
        total_token_count = 5

    class FakeResponse:
        text = "Cached answer about Sigiriya."
        usage_metadata = FakeUsage()

    fake_gemini = mocker.MagicMock()
    fake_gemini.generate_content.return_value = FakeResponse()
    rag = _make_rag(gemini=fake_gemini, collection=fake_chroma)

    spy = mocker.spy(fake_chroma, "query")
    first = rag.query("What's the best time to visit Sigiriya?")
    second = rag.query("What's the best time to visit Sigiriya?")

    assert first["response"] == second["response"]
    assert first["cached"] is False
    assert second["cached"] is True
    assert spy.call_count == 1


def test_prompt_includes_retrieved_chunks(fake_chroma, mocker, gemini_settings):
    class FakeResponse:
        text = "Plan answer"
        usage_metadata = None

    fake_gemini = mocker.MagicMock()
    fake_gemini.generate_content.return_value = FakeResponse()
    rag = _make_rag(gemini=fake_gemini, collection=fake_chroma)

    rag.query("Plan a Sigiriya visit")

    fake_gemini.generate_content.assert_called()
    prompt = fake_gemini.generate_content.call_args.args[0]
    assert "LankaGuide AI" in prompt
    assert "RETRIEVED KNOWLEDGE" in prompt
    assert "Plan a Sigiriya visit" in prompt


def test_itinerary_duplicate_detection_flags_near_identical_days():
    text = """
**Day 1**
- Sigiriya Rock Fortress
- Dambulla Cave Temple

**Day 2**
- Sigiriya Rock Fortress
- Dambulla Cave Temple

**Day 3**
- Kandy Lake
- Temple of the Tooth
""".strip()
    assert _itinerary_response_is_duplicate(text, expected_days=3) is True


def test_itinerary_duplicate_detection_accepts_distinct_days():
    text = """
**Day 1**
- Sigiriya Rock Fortress
- Dambulla Cave Temple

**Day 2**
- Temple of the Tooth
- Royal Botanical Gardens

**Day 3**
- Galle Fort
- Unawatuna Beach
""".strip()
    assert _itinerary_response_is_duplicate(text, expected_days=3) is False
