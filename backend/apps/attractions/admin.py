from django.contrib import admin

from .models import Attraction, District, MediaAsset


class MediaAssetInline(admin.TabularInline):
    model = MediaAsset
    extra = 0


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ("name", "province", "climate_zone")
    search_fields = ("name", "province")
    list_filter = ("climate_zone", "province")


@admin.register(Attraction)
class AttractionAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "district",
        "category",
        "crowd_index",
        "trend_score",
    )
    list_filter = ("category", "district__province")
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [MediaAssetInline]


@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    list_display = ("type", "attraction", "is_featured", "attribution")
    list_filter = ("type", "is_featured")
