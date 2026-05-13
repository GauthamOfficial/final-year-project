# Align SafetyAlert indexes with models.py (active, -created_at).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("alerts", "0001_initial"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="safetyalert",
            name="safety_aler_active_f4c875_idx",
        ),
        migrations.RemoveIndex(
            model_name="safetyalert",
            name="safety_aler_distric_2b81ec_idx",
        ),
        migrations.AddIndex(
            model_name="safetyalert",
            index=models.Index(
                fields=["active", "-created_at"],
                name="safety_aler_active_e25167_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="safetyalert",
            index=models.Index(
                fields=["district", "active", "-created_at"],
                name="safety_aler_distric_0e5972_idx",
            ),
        ),
    ]
