"""Routes for the `vision` app — Prompt 4C."""

from django.urls import path

from .views import VisionIdentifyView

app_name = "vision"

urlpatterns = [
    path("identify/", VisionIdentifyView.as_view(), name="identify"),
]
