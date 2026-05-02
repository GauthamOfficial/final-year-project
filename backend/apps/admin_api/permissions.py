"""Admin-only permission used across the admin_api app."""

from __future__ import annotations

from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    """Allow only authenticated users with `is_staff` or `role == 'admin'`."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or user.is_staff:
            return True
        return getattr(user, "role", None) == "admin"
