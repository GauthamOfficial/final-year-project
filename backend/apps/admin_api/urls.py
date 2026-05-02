"""Routes for the admin dashboard API."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AdminAttractionViewSet,
    AdminChatViewSet,
    AdminDistrictViewSet,
    AdminItineraryViewSet,
    AdminMediaViewSet,
    AdminReviewViewSet,
    AdminUserViewSet,
    CorpusStatsView,
    IngestKnowledgeView,
    KpiView,
)

app_name = "admin_api"

router = DefaultRouter()
router.register(r"users", AdminUserViewSet, basename="admin-users")
router.register(r"districts", AdminDistrictViewSet, basename="admin-districts")
router.register(
    r"attractions", AdminAttractionViewSet, basename="admin-attractions"
)
router.register(r"media", AdminMediaViewSet, basename="admin-media")
router.register(r"itineraries", AdminItineraryViewSet, basename="admin-itineraries")
router.register(r"chat-sessions", AdminChatViewSet, basename="admin-chat-sessions")
router.register(r"reviews", AdminReviewViewSet, basename="admin-reviews")

urlpatterns = [
    path("kpis/", KpiView.as_view(), name="kpis"),
    path("corpus/", CorpusStatsView.as_view(), name="corpus"),
    path("ingest/", IngestKnowledgeView.as_view(), name="ingest"),
    path("", include(router.urls)),
]
