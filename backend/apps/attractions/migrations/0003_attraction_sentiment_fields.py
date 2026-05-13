# Generated manually for attraction sentiment (Gap 3 — tourism trend mining).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("attractions", "0002_attraction_wikipedia_title_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="attraction",
            name="sentiment_score",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="attraction",
            name="sentiment_label",
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name="attraction",
            name="sentiment_summary",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="attraction",
            name="sentiment_updated_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="attraction",
            name="positive_pct",
            field=models.IntegerField(default=0),
        ),
    ]
