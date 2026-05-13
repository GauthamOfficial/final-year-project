# Generated manually for SafetyAlert

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("attractions", "0004_seasonaldata"),
    ]

    operations = [
        migrations.CreateModel(
            name="SafetyAlert",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=300)),
                ("body", models.TextField()),
                (
                    "severity",
                    models.CharField(
                        choices=[
                            ("info", "Info"),
                            ("warning", "Warning"),
                            ("danger", "Danger"),
                        ],
                        default="info",
                        max_length=10,
                    ),
                ),
                ("source_url", models.URLField(blank=True)),
                (
                    "source_name",
                    models.CharField(blank=True, max_length=100),
                ),
                ("active", models.BooleanField(default=True)),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "district",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="alerts",
                        to="attractions.district",
                    ),
                ),
            ],
            options={
                "db_table": "safety_alerts",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="safetyalert",
            index=models.Index(
                fields=["active", "created_at"],
                name="safety_aler_active_f4c875_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="safetyalert",
            index=models.Index(
                fields=["district", "active", "created_at"],
                name="safety_aler_distric_2b81ec_idx",
            ),
        ),
    ]
