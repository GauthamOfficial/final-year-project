from django.db import models


class SafetyAlert(models.Model):
    """Travel / weather advisory surfaced to visitors (Gap 7 — health & safety)."""

    class Severity(models.TextChoices):
        INFO = "info", "Info"
        WARNING = "warning", "Warning"
        DANGER = "danger", "Danger"

    district = models.ForeignKey(
        "attractions.District",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="alerts",
    )
    title = models.CharField(max_length=300)
    body = models.TextField()
    severity = models.CharField(
        max_length=10,
        choices=Severity.choices,
        default=Severity.INFO,
    )
    source_url = models.URLField(blank=True)
    source_name = models.CharField(max_length=100, blank=True)
    active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "safety_alerts"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["active", "-created_at"]),
            models.Index(fields=["district", "active", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.severity}: {self.title[:60]}"
