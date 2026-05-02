"""DRF serializers for the chat endpoints (PRD §8.3)."""

from __future__ import annotations

from rest_framework import serializers

from apps.core.models import Language

from .models import ChatMessage, ChatSession


class ChatMessageRequestSerializer(serializers.Serializer):
    """Body schema for `POST /api/v1/chat/message/` (PRD §8.3)."""

    session_id = serializers.IntegerField(required=False, allow_null=True)
    message = serializers.CharField(min_length=1, max_length=4000)
    language = serializers.ChoiceField(
        choices=Language.choices, default=Language.EN
    )


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = [
            "id",
            "session",
            "role",
            "content",
            "retrieved_docs",
            "tokens_used",
            "created_at",
        ]
        read_only_fields = fields


class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = ["id", "visitor", "started_at", "messages"]
        read_only_fields = fields
