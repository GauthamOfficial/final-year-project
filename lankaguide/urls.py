"""
Top-level URL configuration for the LankaGuide AI project.

All API routes live under `/api/v1/` (PRD Section 8.1). Each app exposes
its own `urls.py` so feature work stays isolated. Endpoints are stubs at
this scaffolding stage — the actual ViewSets land in Prompt sequences 2-4.
"""

from django.contrib import admin
from django.urls import include, path

from apps.core.views import api_root, healthcheck

API_PREFIX = "api/v1/"

urlpatterns = [
    path("admin/", admin.site.urls),
    # Service liveness + API discovery root
    path("", api_root, name="api-root"),
    path("healthz/", healthcheck, name="healthcheck"),
    # Versioned API namespace
    path(f"{API_PREFIX}", include("apps.core.urls")),
    path(f"{API_PREFIX}attractions/", include("apps.attractions.urls")),
    path(f"{API_PREFIX}chat/", include("apps.chat.urls")),
    path(f"{API_PREFIX}itinerary/", include("apps.itinerary.urls")),
    path(f"{API_PREFIX}vision/", include("apps.vision.urls")),
    path(f"{API_PREFIX}trends/", include("apps.sentiment.urls")),
    path(f"{API_PREFIX}alerts/", include("apps.alerts.urls")),
    path(f"{API_PREFIX}analytics/", include("apps.analytics.urls")),
]
