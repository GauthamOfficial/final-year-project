from django.contrib import admin

from apps.alerts.models import SafetyAlert


@admin.register(SafetyAlert)
class SafetyAlertAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "severity",
        "district",
        "active",
        "source_name",
        "created_at",
    )
    list_filter = ("severity", "active", "created_at")
    search_fields = ("title", "body", "source_name")
    raw_id_fields = ("district",)
    date_hierarchy = "created_at"
