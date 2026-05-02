"""Core service-level views: a discoverable API root and health checks."""

from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse


@api_view(["GET"])
@permission_classes([AllowAny])
def api_root(request):
    """Discoverable index for the v1 API surface."""
    base = "api-v1:"
    return Response(
        {
            "service": "LankaGuide",
            "version": "1.0.0",
            "endpoints": {
                "ping": reverse(f"{base}ping", request=request),
                "auth": request.build_absolute_uri("/api/v1/auth/"),
                "attractions": request.build_absolute_uri("/api/v1/attractions/"),
                "chat": request.build_absolute_uri("/api/v1/chat/"),
                "itinerary": request.build_absolute_uri("/api/v1/itinerary/"),
                "vision": request.build_absolute_uri("/api/v1/vision/"),
                "trends": request.build_absolute_uri("/api/v1/trends/"),
                "alerts": request.build_absolute_uri("/api/v1/alerts/"),
                "analytics": request.build_absolute_uri("/api/v1/analytics/"),
                "weather": request.build_absolute_uri("/api/v1/weather/"),
                "routing": request.build_absolute_uri("/api/v1/routing/"),
                "translate": request.build_absolute_uri("/api/v1/translate/"),
            },
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def ping(request):
    return Response({"status": "ok", "service": "lankaguide-api"})


def healthcheck(_request):
    return JsonResponse({"status": "healthy"})
