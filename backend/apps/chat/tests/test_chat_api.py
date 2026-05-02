"""DRF API tests for `POST /api/v1/chat/message/`."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.chat.models import ChatMessage

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="tourist@example.com", password="test12345", full_name="Tourist Test"
    )


@pytest.fixture
def client(user) -> APIClient:
    c = APIClient()
    c.force_authenticate(user=user)
    return c


def test_post_chat_message_happy_path(client, mocker, settings):
    settings.GEMINI_API_KEY = "test-key"
    mocker.patch(
        "apps.chat.services.RAGService",
        side_effect=lambda *a, **k: _stub_rag_service("Stubbed answer"),
    )

    url = reverse("chat:message")
    response = client.post(
        url,
        {"message": "Hello", "language": "en"},
        format="json",
    )
    assert response.status_code == 201, response.content
    data = response.json()
    assert data["response"] == "Stubbed answer"
    assert data["session_id"]
    assert ChatMessage.objects.count() == 2


def test_post_chat_message_validates_message(client, settings):
    settings.GEMINI_API_KEY = "test-key"
    url = reverse("chat:message")
    response = client.post(url, {"language": "en"}, format="json")
    assert response.status_code == 400
    assert "message" in response.json()


def test_post_chat_message_rejects_empty_string(client, settings):
    settings.GEMINI_API_KEY = "test-key"
    url = reverse("chat:message")
    response = client.post(
        url, {"message": "", "language": "en"}, format="json"
    )
    assert response.status_code == 400


def test_post_chat_message_returns_503_when_gemini_missing(client, settings):
    settings.GEMINI_API_KEY = ""
    url = reverse("chat:message")
    response = client.post(
        url, {"message": "anything", "language": "en"}, format="json"
    )
    assert response.status_code == 503


def test_post_chat_message_requires_auth():
    c = APIClient()
    url = reverse("chat:message")
    response = c.post(url, {"message": "Hello", "language": "en"}, format="json")
    assert response.status_code == 401


def _stub_rag_service(text: str):
    class _S:
        def query(self, *args, **kwargs):
            return {
                "response": text,
                "sources": [{"doc_id": "x", "title": "x", "relevance": 0.9}],
                "tokens_used": 7,
                "backend": "stub",
            }

    return _S()
