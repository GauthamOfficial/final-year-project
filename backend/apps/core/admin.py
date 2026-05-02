from django.contrib import admin

from .models import Visitor


@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):
    list_display = ("id", "session_token_short", "language", "created_at", "updated_at")
    list_filter = ("language",)
    search_fields = ("session_token",)
    readonly_fields = ("session_token", "created_at", "updated_at")

    @admin.display(description="Token")
    def session_token_short(self, obj: Visitor) -> str:
        return f"{obj.session_token[:16]}…"
