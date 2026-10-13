"""Root URL configuration."""

from django.contrib import admin
from django.urls import path

from config.api import api
from core.views import healthz

urlpatterns = [
    path("healthz", healthz, name="healthz"),
    path("api/v1/", api.urls),
    # The operator console is Django admin, not part of the REST API (`ADR-0007`, `API.md` §9).
    # Access is gated by `is_staff`; `M5.2`'s runbook entry covers making an operator.
    path("admin/", admin.site.urls),
]
