"""Non-API views: liveness and, later, operational endpoints."""

from django.http import HttpRequest, JsonResponse

from core.logging import get_request_id


def healthz(request: HttpRequest) -> JsonResponse:
    """Liveness probe; deliberately touches no models (see `API.md` section 9)."""
    return JsonResponse({"status": "ok", "request_id": get_request_id()})
