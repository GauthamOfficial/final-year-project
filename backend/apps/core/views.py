"""
Core service-level views: health check + a discoverable API root.

These exist so the project boots end-to-end immediately after scaffolding
(Prompt 1A) and so smoke tests have something concrete to target before the
feature ViewSets land in Prompt sequences 2-4.
"""

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
            "service": "LankaGuide AI",
            "version": "0.1.0",
            "docs": "See LankaGuide_AI_PRD.md (Section 8) for the full API contract.",
            "endpoints": {
                "ping": reverse(f"{base}ping", request=request),
                "attractions": request.build_absolute_uri("/api/v1/attractions/"),
                "chat": request.build_absolute_uri("/api/v1/chat/"),
                "itinerary": request.build_absolute_uri("/api/v1/itinerary/"),
                "vision": request.build_absolute_uri("/api/v1/vision/"),
                "trends": request.build_absolute_uri("/api/v1/trends/"),
                "alerts": request.build_absolute_uri("/api/v1/alerts/"),
                "analytics": request.build_absolute_uri("/api/v1/analytics/"),
            },
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def ping(request):
    return Response({"status": "ok", "service": "lankaguide-api"})


def healthcheck(_request):
    """Plain-Django health endpoint suitable for AWS target-group checks."""
    return JsonResponse({"status": "healthy"})
