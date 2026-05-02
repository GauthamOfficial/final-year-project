from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "attraction",
        "source",
        "sentiment_label",
        "sentiment_score",
        "ingested_at",
    )
    list_filter = ("source", "sentiment_label")
    search_fields = ("body", "external_id")
