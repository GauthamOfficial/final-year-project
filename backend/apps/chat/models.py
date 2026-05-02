"""
Chat persistence models (PRD §7.1 — `chat_sessions`, `chat_messages`).
"""

from __future__ import annotations

from django.db import models

from apps.core.models import Visitor


class Role(models.TextChoices):
    USER = "user", "User"
    ASSISTANT = "assistant", "Assistant"


class ChatSession(models.Model):
    visitor = models.ForeignKey(
        Visitor, on_delete=models.CASCADE, related_name="chat_sessions"
    )
    started_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_sessions"
        ordering = ["-started_at"]

    def __str__(self) -> str:
        return f"Session<{self.id}@{self.visitor_id}>"


class ChatMessage(models.Model):
    session = models.ForeignKey(
        ChatSession, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=10, choices=Role.choices)
    content = models.TextField()
    # JSON array: [{"chroma_id": "...", "title": "...", "score": 0.94}, ...]
    retrieved_docs = models.JSONField(default=list, blank=True)
    tokens_used = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_messages"
        ordering = ["created_at"]
        indexes = [models.Index(fields=["session", "created_at"])]

    def __str__(self) -> str:
        return f"{self.role}: {self.content[:40]}…"
