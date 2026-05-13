from rest_framework import serializers

from apps.alerts.models import SafetyAlert


class SafetyAlertSerializer(serializers.ModelSerializer):
    district_name = serializers.SerializerMethodField()

    class Meta:
        model = SafetyAlert
        fields = (
            "id",
            "district_name",
            "title",
            "body",
            "severity",
            "source_name",
            "source_url",
            "created_at",
        )
        read_only_fields = fields

    def get_district_name(self, obj: SafetyAlert) -> str | None:
        return obj.district.name if obj.district_id else None
