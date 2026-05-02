from django.contrib import admin

from .models import Itinerary, ItineraryDay, ItineraryStop


class StopInline(admin.TabularInline):
    model = ItineraryStop
    extra = 0


class DayInline(admin.StackedInline):
    model = ItineraryDay
    extra = 0


@admin.register(Itinerary)
class ItineraryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "visitor",
        "start_date",
        "end_date",
        "status",
    )
    list_filter = ("status", "group_type")
    search_fields = ("title", "share_token")
    inlines = [DayInline]


@admin.register(ItineraryDay)
class ItineraryDayAdmin(admin.ModelAdmin):
    list_display = ("itinerary", "day_number", "district", "ai_generated")
    inlines = [StopInline]


@admin.register(ItineraryStop)
class ItineraryStopAdmin(admin.ModelAdmin):
    list_display = ("day", "stop_order", "attraction", "duration_mins")
