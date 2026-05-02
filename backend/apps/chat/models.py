"""Chat persistence models — sessions and messages tied to authenticated users."""

from __future__ import annotations

from django.conf import settings
from django.db import models


class Role(models.TextChoices):
    USER = "user", "User"
    ASSISTANT = "assistant", "Assistant"


class ChatSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_sessions",
    )
    title = models.CharField(max_length=200, blank=True)
    language = models.CharField(max_length=2, default="en")
    started_at = models.DateTimeField(auto_now_add=True)
    last_activity_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "chat_sessions"
        ordering = ["-last_activity_at"]

    def __str__(self) -> str:
        return f"Session<{self.id}@{self.user_id}>"


class ChatMessage(models.Model):
    session = models.ForeignKey(
        ChatSession, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=10, choices=Role.choices)
    content = models.TextField()
    retrieved_docs = models.JSONField(default=list, blank=True)
    tokens_used = models.PositiveIntegerField(default=0)
    backend = models.CharField(max_length=32, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_messages"
        ordering = ["created_at"]
        indexes = [models.Index(fields=["session", "created_at"])]

    def __str__(self) -> str:
        snippet = self.content[:40].replace("\n", " ")
        return f"{self.role}: {snippet}"
