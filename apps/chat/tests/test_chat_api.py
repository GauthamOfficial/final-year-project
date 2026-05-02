"""DRF API tests for `POST /api/v1/chat/message/` (Prompt 6A)."""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.chat.models import ChatMessage
from apps.core.models import Visitor


pytestmark = pytest.mark.django_db


@pytest.fixture
def client() -> APIClient:
    return APIClient()


def test_post_chat_message_happy_path(client, mocker):
    """A valid POST creates a session, persists both messages, and returns the contract from PRD §8.3."""
    mocker.patch(
        "apps.chat.services.RAGService",
        side_effect=lambda *a, **k: _stub_rag_service("Stubbed answer"),
    )

    url = reverse("chat:message")
    response = client.post(
        url,
        {"message": "Hello", "language": "en"},
        format="json",
        HTTP_X_SESSION_TOKEN="visitor-1",
    )
    assert response.status_code == 201, response.content
    data = response.json()
    assert data["response"] == "Stubbed answer"
    assert data["session_id"]
    assert ChatMessage.objects.count() == 2  # user + assistant persisted
    assert Visitor.objects.filter(session_token="visitor-1").exists()


def test_post_chat_message_validates_message(client):
    url = reverse("chat:message")
    response = client.post(url, {"language": "en"}, format="json")
    assert response.status_code == 400
    assert "message" in response.json()


def test_post_chat_message_rejects_empty_string(client):
    url = reverse("chat:message")
    response = client.post(
        url, {"message": "", "language": "en"}, format="json"
    )
    assert response.status_code == 400


def test_post_chat_message_falls_back_when_rag_explodes(client, mocker):
    """If RAGService raises, we still return the assistant stub fallback (no 500)."""
    mocker.patch(
        "apps.chat.services.RAGService",
        side_effect=RuntimeError("boom"),
    )
    url = reverse("chat:message")
    response = client.post(
        url,
        {"message": "anything", "language": "en"},
        format="json",
        HTTP_X_SESSION_TOKEN="visitor-2",
    )
    assert response.status_code == 201
    assert "stub" in response.json()["response"].lower()


def _stub_rag_service(text: str):
    """Helper that returns a service-shaped object whose .query() returns a fixed payload."""

    class _S:
        def query(self, *args, **kwargs):
            return {
                "response": text,
                "sources": [
                    {"doc_id": "x", "title": "x", "relevance": 0.9}
                ],
                "tokens_used": 7,
            }

    return _S()
