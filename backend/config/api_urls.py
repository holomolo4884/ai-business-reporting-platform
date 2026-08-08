from django.urls import include, path

from config.api import health_check

app_name = "api"

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("", include("accounts.urls")),
]
