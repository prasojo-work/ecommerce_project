# pyright: reportArgumentType=false
# django-environ's type stubs mis-type the `default` parameter (scoped workaround).
"""Development settings."""

from .base import *
from .base import env

DEBUG = env.bool("DJANGO_DEBUG", default=True)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
