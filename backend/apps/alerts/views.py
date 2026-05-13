from django.db import models
from django.db.models import Case, IntegerField, When
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.alerts.models import SafetyAlert
from apps.alerts.serializers import SafetyAlertSerializer


def _truthy(val: str | None) -> bool:
    if val is None:
        return True
    return str(val).lower() in ("1", "true", "yes")


class AlertListView(APIView):
    """GET /api/v1/alerts/ — public read for travel advisories."""

    permission_classes = [AllowAny]

    def get(self, request):
        qs = SafetyAlert.objects.select_related("district").all()
        if _truthy(request.query_params.get("active", "true")):
            qs = qs.filter(active=True)
            now = timezone.now()
            qs = qs.filter(
                models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=now)
            )

        did = request.query_params.get("district_id")
        if did:
            qs = qs.filter(district_id=did)
        severity = request.query_params.get("severity")
        if severity:
            qs = qs.filter(severity=severity)

        qs = qs.annotate(
            severity_order=Case(
                When(severity=SafetyAlert.Severity.DANGER, then=0),
                When(severity=SafetyAlert.Severity.WARNING, then=1),
                When(severity=SafetyAlert.Severity.INFO, then=2),
                default=3,
                output_field=IntegerField(),
            )
        ).order_by("severity_order", "-created_at")

        ser = SafetyAlertSerializer(qs, many=True)
        return Response(ser.data)


class AlertActiveCountView(APIView):
    """GET /api/v1/alerts/active-count/ — counts for navbar badge."""

    permission_classes = [AllowAny]

    def get(self, request):
        now = timezone.now()
        base = SafetyAlert.objects.filter(active=True).filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=now)
        )
        data = {
            "total": base.count(),
            "danger": base.filter(severity=SafetyAlert.Severity.DANGER).count(),
            "warning": base.filter(severity=SafetyAlert.Severity.WARNING).count(),
            "info": base.filter(severity=SafetyAlert.Severity.INFO).count(),
        }
        return Response(data)
