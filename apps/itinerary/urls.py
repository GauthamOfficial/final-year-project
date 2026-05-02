"""Routes for the `itinerary` app — Prompt 2C."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import GenerateItineraryView, ItineraryViewSet

app_name = "itinerary"

router = DefaultRouter()
router.register(r"", ItineraryViewSet, basename="itineraries")

urlpatterns = [
    path("generate/", GenerateItineraryView.as_view(), name="generate"),
    path("", include(router.urls)),
]
