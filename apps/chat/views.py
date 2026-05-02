"""
Chat endpoints (PRD §5.1, §8.2, §8.3).

`POST /api/v1/chat/message/` is the workhorse: it persists the user message,
calls `RAGService.query()`, persists the assistant reply, and returns the
shape from PRD §8.3. The actual `RAGService` lands in Prompt 4A; this view
imports it lazily so Prompt 2B is functional even before that prompt runs
(it falls back to a deterministic stub).
"""

from __future__ import annotations

import logging

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import Visitor

from .models import ChatMessage, ChatSession, Role
from .serializers import (
    ChatMessageRequestSerializer,
    ChatMessageSerializer,
    ChatSessionSerializer,
)

logger = logging.getLogger("lankaguide.chat")


def _resolve_visitor(request) -> Visitor:
    token = request.headers.get("X-Session-Token") or ""
    visitor, _ = Visitor.get_or_create_by_token(token)
    return visitor


def _resolve_session(visitor: Visitor, session_id: int | None) -> ChatSession:
    if session_id:
        try:
            return ChatSession.objects.get(id=session_id, visitor=visitor)
        except ChatSession.DoesNotExist:
            logger.info(
                "Requested chat session %s not owned by visitor %s — creating fresh",
                session_id,
                visitor.id,
            )
    return ChatSession.objects.create(visitor=visitor)


def _stub_rag_response(message: str, language: str) -> dict:
    """
    Deterministic stand-in used until `RAGService` (Prompt 4A) is wired up.
    Keeps the contract from PRD §8.3 intact so the frontend can be developed
    against a working endpoint before Gemini credentials are provisioned.
    """
    return {
        "response": (
            f"[stub:{language}] I received your question — "
            f"'{message.strip()[:120]}' — "
            "but the RAG service is not configured yet. "
            "Wire up GEMINI_API_KEY and run Prompt 4A."
        ),
        "sources": [],
        "tokens_used": 0,
    }


class ChatMessageView(APIView):
    """`POST /api/v1/chat/message/` — sync wrapper around `RAGService.query()`."""

    def post(self, request):
        ser = ChatMessageRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        visitor = _resolve_visitor(request)
        if visitor.language != data["language"]:
            visitor.language = data["language"]
            visitor.save(update_fields=["language", "updated_at"])

        session = _resolve_session(visitor, data.get("session_id"))

        user_msg = ChatMessage.objects.create(
            session=session,
            role=Role.USER,
            content=data["message"],
        )

        try:
            from apps.chat.services import RAGService  # local import; lazy

            rag = RAGService()
            history = list(
                session.messages.order_by("-created_at")
                .exclude(id=user_msg.id)
                .values("role", "content")[:8]
            )
            history.reverse()
            rag_result = rag.query(
                user_message=data["message"],
                session_history=history,
                language=data["language"],
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("RAGService unavailable, falling back to stub: %s", exc)
            rag_result = _stub_rag_response(data["message"], data["language"])

        assistant_msg = ChatMessage.objects.create(
            session=session,
            role=Role.ASSISTANT,
            content=rag_result["response"],
            retrieved_docs=rag_result.get("sources", []),
            tokens_used=rag_result.get("tokens_used", 0),
        )

        return Response(
            {
                "message_id": assistant_msg.id,
                "session_id": session.id,
                "response": assistant_msg.content,
                "sources": assistant_msg.retrieved_docs,
                "tokens_used": assistant_msg.tokens_used,
                "user_message": ChatMessageSerializer(user_msg).data,
            },
            status=status.HTTP_201_CREATED,
        )


class ChatSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """`GET /api/v1/chat/sessions/{id}/` — return session + messages."""

    serializer_class = ChatSessionSerializer

    def get_queryset(self):
        visitor = _resolve_visitor(self.request)
        return (
            ChatSession.objects.filter(visitor=visitor)
            .prefetch_related("messages")
            .order_by("-started_at")
        )

    @action(detail=True, methods=["get"], url_path="history")
    def history(self, request, pk=None):
        session = self.get_object()
        ser = ChatMessageSerializer(session.messages.all(), many=True)
        return Response({"session_id": session.id, "messages": ser.data})
