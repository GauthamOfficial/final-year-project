"""
Custom user model for LankaGuide.

Email-as-username, with a `role` field for RBAC (tourist / editor / admin) and
a `language` preference that drives multilingual responses across the app.
"""

from __future__ import annotations

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class Language(models.TextChoices):
    EN = "en", "English"
    SI = "si", "Sinhala"
    TA = "ta", "Tamil"


class Role(models.TextChoices):
    TOURIST = "tourist", "Tourist"
    EDITOR = "editor", "Editor"
    ADMIN = "admin", "Admin"


class UserManager(BaseUserManager):
    """Email-as-username manager."""

    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra):
        if not email:
            raise ValueError("Users must have an email address.")
        email = self.normalize_email(email)
        username = extra.pop("username", None) or email
        user = self.model(email=email, username=username, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        extra.setdefault("role", Role.TOURIST)
        return self._create_user(email, password, **extra)

    def create_superuser(self, email: str, password: str | None = None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("role", Role.ADMIN)
        if extra.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra)


class User(AbstractUser):
    """Authenticated user replacing the legacy anonymous Visitor."""

    email = models.EmailField(_("email address"), unique=True)
    full_name = models.CharField(max_length=200, blank=True)
    avatar_url = models.URLField(blank=True)
    role = models.CharField(
        max_length=16, choices=Role.choices, default=Role.TOURIST
    )
    language = models.CharField(
        max_length=2, choices=Language.choices, default=Language.EN
    )
    home_country = models.CharField(max_length=80, blank=True)
    interests = models.JSONField(default=list, blank=True)
    onboarding_complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = UserManager()

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.email

    @property
    def display_name(self) -> str:
        return self.full_name or self.email.split("@")[0]

    @property
    def is_admin_role(self) -> bool:
        return self.role == Role.ADMIN or self.is_superuser
