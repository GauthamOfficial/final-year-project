"""Routes for the `chat` app — Prompt 2B."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ChatMessageView, ChatSessionViewSet

app_name = "chat"

router = DefaultRouter()
router.register(r"sessions", ChatSessionViewSet, basename="sessions")

urlpatterns = [
    path("message/", ChatMessageView.as_view(), name="message"),
    path("", include(router.urls)),
]
