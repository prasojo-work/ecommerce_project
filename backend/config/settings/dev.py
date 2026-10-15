# pyright: reportArgumentType=false
# django-environ's type stubs mis-type the `default` parameter (scoped workaround).
"""Development settings."""

from .base import *
from .base import env

DEBUG = env.bool("DJANGO_DEBUG", default=True)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# Serve the admin's CSS and JS straight from the app directories, so a working console in development
# does not depend on having run `collectstatic` first. Production serves the collected, hashed copy
# instead (`prod.py`), which is built into the image.
WHITENOISE_USE_FINDERS = True
