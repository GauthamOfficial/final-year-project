"""
Shared cross-cutting models for LankaGuide AI.

The PRD's `users` table (§7.1) is *not* Django's auth user — it represents an
anonymous tourist session keyed by `session_token`. We expose it as `Visitor`
to avoid clashing with `django.contrib.auth.User`, but keep `db_table='users'`
so the SQL DDL exactly matches the PRD.
"""

from __future__ import annotations

import secrets

from django.db import models


class Language(models.TextChoices):
    EN = "en", "English"
    SI = "si", "Sinhala"
    TA = "ta", "Tamil"


def _new_session_token() -> str:
    return secrets.token_urlsafe(32)[:128]


class Visitor(models.Model):
    """Anonymous, session-bound tourist profile (PRD §5.1, §7.1 `users`)."""

    session_token = models.CharField(
        max_length=128, unique=True, default=_new_session_token, db_index=True
    )
    language = models.CharField(
        max_length=2, choices=Language.choices, default=Language.EN
    )
    budget_range = models.CharField(max_length=32, blank=True)
    # JSON list of interest tags, e.g. ["beach", "culture"].
    interests = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "users"
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"Visitor<{self.session_token[:10]}…>"

    @classmethod
    def get_or_create_by_token(
        cls,
        token: str | None,
        *,
        language: str | None = None,
    ) -> tuple["Visitor", bool]:
        """
        Convenience helper used by every endpoint that takes
        `X-Session-Token` (PRD §8.1). Creates a Visitor on first sight.
        """
        if token:
            obj, created = cls.objects.get_or_create(
                session_token=token,
                defaults={"language": language or cls._meta.get_field("language").default},
            )
            return obj, created
        obj = cls.objects.create(language=language or cls._meta.get_field("language").default)
        return obj, True
