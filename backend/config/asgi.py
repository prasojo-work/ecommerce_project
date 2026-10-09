"""ASGI entrypoint (served with Uvicorn; see ADR-0006)."""

from config.env import configure_settings

configure_settings()

from django.core.asgi import get_asgi_application  # noqa: E402

application = get_asgi_application()
