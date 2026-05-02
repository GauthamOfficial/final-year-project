"""Routes for the `vision` app — Prompt 4C."""

from django.urls import path

from .views import IdentifyView

app_name = "vision"

urlpatterns = [
    path("identify/", IdentifyView.as_view(), name="identify"),
]
