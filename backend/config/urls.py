"""Root URL configuration."""

from django.urls import path

from config.api import api
from core.views import healthz

urlpatterns = [
    path("healthz", healthz, name="healthz"),
    path("api/v1/", api.urls),
]
