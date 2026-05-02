"""Password reset + change endpoints."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.test import APIClient

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def mail_backend(settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"


def test_password_reset_request_always_succeeds(mail_backend):
    c = APIClient()
    r = c.post(
        "/api/v1/auth/password/reset/",
        {"email": "nobody@example.com"},
        format="json",
    )
    assert r.status_code == 200


def test_password_reset_confirm_updates_password(mail_backend):
    user = User.objects.create_user(
        email="u@example.com", password="OldPass123!", full_name="U"
    )
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    c = APIClient()
    r = c.post(
        "/api/v1/auth/password/reset/confirm/",
        {
            "uid": uid,
            "token": token,
            "new_password": "NewPass456!",
        },
        format="json",
    )
    assert r.status_code == 200
    user.refresh_from_db()
    assert user.check_password("NewPass456!")


def test_password_change_requires_old_password():
    user = User.objects.create_user(
        email="c@example.com", password="Correct123!", full_name="C"
    )
    c = APIClient()
    c.force_authenticate(user=user)
    bad = c.post(
        "/api/v1/auth/password/change/",
        {"old_password": "wrong", "new_password": "Other456!"},
        format="json",
    )
    assert bad.status_code == 400

    ok = c.post(
        "/api/v1/auth/password/change/",
        {"old_password": "Correct123!", "new_password": "Other456!"},
        format="json",
    )
    assert ok.status_code == 200
    user.refresh_from_db()
    assert user.check_password("Other456!")
