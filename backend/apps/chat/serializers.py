"""Serializers for the chat endpoints."""

from __future__ import annotations

from rest_framework import serializers

from apps.core.models import Language

from .models import ChatMessage, ChatSession


class ChatMessageRequestSerializer(serializers.Serializer):
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
            "backend",
            "created_at",
        ]
        read_only_fields = fields


class ChatSessionListSerializer(serializers.ModelSerializer):
    message_count = serializers.SerializerMethodField()
    preview = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = [
            "id",
            "title",
            "language",
            "started_at",
            "last_activity_at",
            "message_count",
            "preview",
        ]

    def get_message_count(self, obj) -> int:
        return obj.messages.count()

    def get_preview(self, obj) -> str:
        first = obj.messages.first()
        if first is None:
            return ""
        text = first.content[:140]
        return text


class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = [
            "id",
            "title",
            "language",
            "started_at",
            "last_activity_at",
            "messages",
        ]
        read_only_fields = fields
