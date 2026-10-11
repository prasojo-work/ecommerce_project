# pyright: reportArgumentType=false
# django-environ's type stubs mis-type the `default` parameter; this scoped directive is the
# workaround. See docs/03-architecture/ARCHITECTURE.md section 10 (configuration over code).
"""Base Django settings shared by every environment.

All environment-specific values are read from the environment (12-factor); see
`docs/03-architecture/ARCHITECTURE.md` section 10 and `ADR-0011`.
"""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="insecure-development-key-change-me")

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "core",
    "accounts",
    "catalog",
]

# Email is the identifier and there is no `username` column (`DATA-MODEL.md` section 2). Declared
# here, before `accounts` has ever been migrated, so the swap never has to be retrofitted onto a
# database that already carries `auth_user`.
AUTH_USER_MODEL = "accounts.User"

# `US-2.1` asks for "email + password with validation". These are Django's four defaults —
# similarity to the user's own details, an 8-character minimum, the common-password list and the
# all-numeric check — applied through `validate_password()`, which the register endpoint calls.
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

MIDDLEWARE = [
    "core.middleware.RequestIDMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": []},
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# Prefer DATABASE_URL (PostgreSQL in every real environment); fall back to SQLite so the
# test suite and a bare checkout run without extra infrastructure.
DATABASE_URL = env("DATABASE_URL", default="")
if DATABASE_URL:
    DATABASES = {"default": env.db_url("DATABASE_URL")}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"json": {"()": "core.logging.JsonFormatter"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "json"}},
    "root": {"handlers": ["console"], "level": env("DJANGO_LOG_LEVEL", default="INFO")},
}
