"""WSGI entrypoint (kept for tooling that expects it)."""

from config.env import configure_settings

configure_settings()

from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()
