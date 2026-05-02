"""Admin API must reject anonymous users and non-admin roles."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

pytestmark = pytest.mark.django_db


def test_admin_kpis_requires_admin_role():
    url = "/api/v1/admin/kpis/"
    anon = APIClient()
    assert anon.get(url).status_code == 401

    tourist = User.objects.create_user(
        email="t@example.com", password="pw12345678", full_name="T"
    )
    assert tourist.role == "tourist"

    c = APIClient()
    c.force_authenticate(user=tourist)
    assert c.get(url).status_code == 403

    tourist.role = "admin"
    tourist.is_staff = True
    tourist.save(update_fields=["role", "is_staff"])
    assert c.get(url).status_code == 200
