# pyright: reportArgumentType=false
# django-environ's type stubs mis-type the `default` parameter (scoped workaround).
"""Production settings.

Turned on only through the environment; the container never ships development defaults.
"""

from django.core.exceptions import ImproperlyConfigured

from .base import *
from .base import env

DEBUG = False
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])

if SECRET_KEY == "insecure-development-key-change-me":
    raise ImproperlyConfigured("DJANGO_SECRET_KEY must be set in production.")

# Transport and browser hardening (see docs/06-quality/SECURITY-BASELINE.md section 6).
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
