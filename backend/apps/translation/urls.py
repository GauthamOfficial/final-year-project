from django.urls import path

from .views import TranslateView

app_name = "translation"

urlpatterns = [
    path("", TranslateView.as_view(), name="translate"),
]
