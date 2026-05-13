"""
Synchronise automatic weather alerts from Open-Meteo.

Cron (every 6 hours on EC2), e.g.:

    0 */6 * * * /var/www/lankaguide/venv/bin/python /var/www/lankaguide/manage.py sync_weather_alerts
"""

from django.core.management.base import BaseCommand

from lankaguide.services.weather_service import WeatherAlertService


class Command(BaseCommand):
    help = "Fetch weather from Open-Meteo and create/update SafetyAlert rows."

    def handle(self, *args, **options):
        svc = WeatherAlertService()
        created, deactivated = svc.sync_weather_alerts()
        self.stdout.write(
            self.style.SUCCESS(
                f"Created {created} alerts, deactivated {deactivated} alerts"
            )
        )
