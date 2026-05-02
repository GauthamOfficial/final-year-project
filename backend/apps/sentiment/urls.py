"""Routes for the `sentiment` app — Prompt 6B / PRD §5.4."""

from django.urls import path

from .views import IngestReviewView, TrendingAttractionsView

app_name = "sentiment"

urlpatterns = [
    path("attractions/", TrendingAttractionsView.as_view(), name="trending"),
    path("reviews/", IngestReviewView.as_view(), name="ingest"),
]
