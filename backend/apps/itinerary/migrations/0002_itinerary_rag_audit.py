# Itinerary RAG audit fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("itinerary", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="itinerary",
            name="retrieved_doc_ids",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="itinerary",
            name="rag_used",
            field=models.BooleanField(default=False),
        ),
    ]
