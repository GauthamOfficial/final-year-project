"""Routes for travel advisories / safety alerts."""

from django.urls import path

from apps.alerts.views import AlertActiveCountView, AlertListView

app_name = "alerts"

urlpatterns = [
    path("", AlertListView.as_view(), name="list"),
    path("active-count/", AlertActiveCountView.as_view(), name="active-count"),
]
