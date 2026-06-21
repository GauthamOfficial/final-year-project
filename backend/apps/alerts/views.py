from django.db import models
from django.db.models import Case, IntegerField, When
from django.utils import timezone
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.alerts.auto_sync import ensure_alerts_fresh
from apps.alerts.models import SafetyAlert
from apps.alerts.serializers import SafetyAlertSerializer


def _truthy(val: str | None) -> bool:
    if val is None:
        return True
    return str(val).lower() in ("1", "true", "yes")


class AlertListView(ListAPIView):
    """GET /api/v1/alerts/ — public read (no global page-size wrapper)."""

    serializer_class = SafetyAlertSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        # Keep live weather alerts fresh without a manual cron run; this is a
        # non-blocking background refresh, throttled to once per interval.
        ensure_alerts_fresh()
        qs = SafetyAlert.objects.select_related("district").all()
        if _truthy(self.request.query_params.get("active", "true")):
            qs = qs.filter(active=True)
            now = timezone.now()
            qs = qs.filter(
                models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=now)
            )

        did = self.request.query_params.get("district_id")
        if did:
            qs = qs.filter(district_id=did)
        severity = self.request.query_params.get("severity")
        if severity:
            qs = qs.filter(severity=severity)

        return qs.annotate(
            severity_order=Case(
                When(severity=SafetyAlert.Severity.DANGER, then=0),
                When(severity=SafetyAlert.Severity.WARNING, then=1),
                When(severity=SafetyAlert.Severity.INFO, then=2),
                default=3,
                output_field=IntegerField(),
            )
        ).order_by("severity_order", "-created_at")


class AlertActiveCountView(APIView):
    """GET /api/v1/alerts/active-count/ — counts for navbar badge."""

    permission_classes = [AllowAny]

    def get(self, request):
        ensure_alerts_fresh()
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
