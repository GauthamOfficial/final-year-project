"""Top-level URL configuration for the LankaGuide API."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.core.views import api_root, healthcheck

API_PREFIX = "api/v1/"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", api_root, name="api-root"),
    path("healthz/", healthcheck, name="healthcheck"),
    path(f"{API_PREFIX}", include("apps.core.urls")),
    path(f"{API_PREFIX}auth/", include("apps.accounts.urls")),
    path(f"{API_PREFIX}attractions/", include("apps.attractions.urls")),
    path(f"{API_PREFIX}chat/", include("apps.chat.urls")),
    path(f"{API_PREFIX}itinerary/", include("apps.itinerary.urls")),
    path(f"{API_PREFIX}vision/", include("apps.vision.urls")),
    path(f"{API_PREFIX}trends/", include("apps.sentiment.urls")),
    path(f"{API_PREFIX}alerts/", include("apps.alerts.urls")),
    path(f"{API_PREFIX}analytics/", include("apps.analytics.urls")),
    path(f"{API_PREFIX}weather/", include("apps.weather.urls")),
    path(f"{API_PREFIX}routing/", include("apps.routing.urls")),
    path(f"{API_PREFIX}translate/", include("apps.translation.urls")),
    path(f"{API_PREFIX}admin/", include("apps.admin_api.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
