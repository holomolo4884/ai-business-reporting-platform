from django.urls import path

from config.api import health_check

app_name = "api"

urlpatterns = [
    path("health/", health_check, name="health_check"),
]
