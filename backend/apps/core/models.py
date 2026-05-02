"""
Cross-cutting models for LankaGuide.

The original anonymous `Visitor` table was retired in favour of
`apps.accounts.User`. We keep the `Language` enum here for backwards
compatibility with any code that imports it from `apps.core.models`.
"""

from __future__ import annotations

from django.db import models


class Language(models.TextChoices):
    EN = "en", "English"
    SI = "si", "Sinhala"
    TA = "ta", "Tamil"
