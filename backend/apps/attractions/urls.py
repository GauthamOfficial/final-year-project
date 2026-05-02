"""
Routes for the `attractions` app — Prompt 2A.

Nests under `/api/v1/attractions/` (see `lankaguide/urls.py`). The DefaultRouter
also registers `districts/` and `media/` collections directly under
`/api/v1/attractions/` for a flat, discoverable surface.
"""

from rest_framework.routers import DefaultRouter

from .views import AttractionsViewSet, DistrictsViewSet, MediaAssetsViewSet

app_name = "attractions"

router = DefaultRouter()
router.register(r"districts", DistrictsViewSet, basename="districts")
router.register(r"media", MediaAssetsViewSet, basename="media")
# `Attractions` is registered last with the empty prefix so that
# `/api/v1/attractions/` returns the attraction list (PRD §8.2).
router.register(r"", AttractionsViewSet, basename="attractions")

urlpatterns = router.urls
