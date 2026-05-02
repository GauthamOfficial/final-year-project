from django.urls import path

from .views import EtaView

app_name = "routing"

urlpatterns = [
    path("eta/", EtaView.as_view(), name="eta"),
]
