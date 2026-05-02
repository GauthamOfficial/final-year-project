"""Chat endpoints. Every endpoint requires an authenticated user."""

from __future__ import annotations

import logging

from django.conf import settings
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ChatMessage, ChatSession, Role
from .serializers import (
    ChatMessageRequestSerializer,
    ChatMessageSerializer,
    ChatSessionListSerializer,
    ChatSessionSerializer,
)

logger = logging.getLogger("lankaguide.chat")


def _resolve_session(user, session_id: int | None, language: str) -> ChatSession:
    if session_id:
        try:
            return ChatSession.objects.get(id=session_id, user=user)
        except ChatSession.DoesNotExist:
            logger.info(
                "Chat session %s not owned by user %s — creating fresh.",
                session_id,
                user.id,
            )
    return ChatSession.objects.create(user=user, language=language)


def _service_unavailable(message: str) -> Response:
    return Response(
        {"detail": message, "code": "service_unavailable"},
        status=status.HTTP_503_SERVICE_UNAVAILABLE,
    )


class ChatMessageView(APIView):
    """`POST /api/v1/chat/message/`."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        ser = ChatMessageRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        user = request.user
        if user.language != data["language"]:
            user.language = data["language"]
            user.save(update_fields=["language", "updated_at"])

        if not getattr(settings, "GEMINI_API_KEY", ""):
            return _service_unavailable(
                "AI service is not configured. The administrator must set GEMINI_API_KEY."
            )

        session = _resolve_session(user, data.get("session_id"), data["language"])

        user_msg = ChatMessage.objects.create(
            session=session,
            role=Role.USER,
            content=data["message"],
        )

        try:
            from apps.chat.services import RAGService

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
            logger.exception("RAGService failed: %s", exc)
            return _service_unavailable(
                "The AI guide is temporarily unavailable. Please retry shortly."
            )

        assistant_msg = ChatMessage.objects.create(
            session=session,
            role=Role.ASSISTANT,
            content=rag_result["response"],
            retrieved_docs=rag_result.get("sources", []),
            tokens_used=rag_result.get("tokens_used", 0),
            backend=rag_result.get("backend", ""),
        )

        if not session.title:
            session.title = data["message"][:80]
            session.save(update_fields=["title", "last_activity_at"])

        return Response(
            {
                "message_id": assistant_msg.id,
                "session_id": session.id,
                "response": assistant_msg.content,
                "sources": assistant_msg.retrieved_docs,
                "tokens_used": assistant_msg.tokens_used,
                "backend": assistant_msg.backend,
                "user_message": ChatMessageSerializer(user_msg).data,
            },
            status=status.HTTP_201_CREATED,
        )


class ChatSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """`GET /api/v1/chat/sessions/` — list current user's chat history."""

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            ChatSession.objects.filter(user=self.request.user)
            .prefetch_related("messages")
            .order_by("-last_activity_at")
        )

    def get_serializer_class(self):
        if self.action == "list":
            return ChatSessionListSerializer
        return ChatSessionSerializer

    @action(detail=True, methods=["get"], url_path="history")
    def history(self, request, pk=None):
        session = self.get_object()
        ser = ChatMessageSerializer(session.messages.all(), many=True)
        return Response({"session_id": session.id, "messages": ser.data})

    @action(detail=True, methods=["delete"], url_path="delete")
    def delete_session(self, request, pk=None):
        session = self.get_object()
        session.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
