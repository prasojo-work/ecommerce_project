# pyright: reportArgumentType=false
# django-environ's type stubs mis-type the `default` parameter; this scoped directive is the
# workaround. See docs/03-architecture/ARCHITECTURE.md section 10 (configuration over code).
"""Base Django settings shared by every environment.

All environment-specific values are read from the environment (12-factor); see
`docs/03-architecture/ARCHITECTURE.md` section 10 and `ADR-0011`.
"""

from pathlib import Path

import environ

from config.env import INSECURE_DEVELOPMENT_KEY
from core.middleware import REQUEST_ID_HEADER

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default=INSECURE_DEVELOPMENT_KEY)

INSTALLED_APPS = [
    # The operator console (`M5.1`, `ADR-0007`). `admin` pulls in sessions and the messages
    # framework, and those two are here for its benefit alone: the REST API is stateless
    # (`ADR-0009`) and reads neither.
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "core",
    "accounts",
    "catalog",
    "cart",
    "orders",
    "payments",
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

# JWT authentication (`ADR-0009`). The signing key defaults to `SECRET_KEY` so a plain checkout
# needs no extra setup; set `JWT_SECRET_KEY` to rotate the two independently in a real deployment.
JWT_SECRET_KEY = env("JWT_SECRET_KEY", default="") or SECRET_KEY
JWT_ALGORITHM = "HS256"

# A short access token and a long refresh token is the whole point of the pair: the access token is
# the one that leaks into a header or a log, so it is the one that expires quickly.
ACCESS_TOKEN_TTL_SECONDS = env.int("ACCESS_TOKEN_TTL_SECONDS", default=15 * 60)
REFRESH_TOKEN_TTL_SECONDS = env.int("REFRESH_TOKEN_TTL_SECONDS", default=14 * 24 * 60 * 60)

# The refresh cookie is the only place the refresh token exists client-side, so its scope is as
# narrow as the routes allow. `Secure` and `SameSite` are raised in production, where the API and
# the web app are genuinely different sites.
REFRESH_COOKIE_NAME = env("REFRESH_COOKIE_NAME", default="lysheim_refresh")
REFRESH_COOKIE_PATH = env("REFRESH_COOKIE_PATH", default="/api/v1/auth")
REFRESH_COOKIE_SECURE = env.bool("REFRESH_COOKIE_SECURE", default=False)
REFRESH_COOKIE_SAMESITE = env("REFRESH_COOKIE_SAMESITE", default="Lax")

# Rate limits for the auth surface (`US-2.2` asks for a rate-limited sign-in; `NFR-3` asks for auth
# rate limiting generally). Django Ninja reads this mapping and each throttle class picks its scope
# out of it, so the numbers are policy rather than code (`ADR-0011`). Values are `requests/period`
# with the periods Ninja parses: s, sec, m, min, h, hour, d, day.
NINJA_DEFAULT_THROTTLE_RATES = {
    # The endpoint actually worth brute-forcing, and so the tightest of the three. Ten is far above
    # what a person needs — a typo costs one — and far below what makes guessing worthwhile.
    "login": "10/min",
    # A person registers once; a script registers until it is stopped.
    "register": "10/hour",
    # Generous on purpose. The client refreshes silently and rarely (an access token lasts 15
    # minutes), so this limit exists to stop a runaway client, not a patient one — and it must never
    # be the reason a real customer is signed out.
    "refresh": "60/min",
    # Authenticated endpoints (`/auth/me`, `/auth/logout`), keyed per account rather than per IP.
    "auth": "240/min",
    # Django's own console sign-in (`SEC-FIND-1.7`). Not a Ninja operation, so `accounts/middleware.py`
    # attaches it rather than a route decorator — but it is a rate like the others and belongs in this
    # mapping. Ten for the same reason `/auth/login` is ten, and the same scope of damage if it were
    # missing: a guessed password here buys the whole catalog and every order in it.
    "admin-login": "10/min",
}

# How many proxies sit in front of the app, which decides whose IP a throttle counts. Ninja keys on
# `X-Forwarded-For` when this is set and on the connection's own address when it is 0 — and it uses
# that header *verbatim* when this is unset, which any client can forge, so leaving the default
# would make every limit below bypassable by sending a different fake header each time.
#
# Zero is right locally. On Render it is **2, not 1**: Render's load balancer appends the address it
# saw, and that address is Cloudflare's edge — Render serves `.onrender.com` through Cloudflare, as
# the deployed API states in its own `server` header. The header the app reads therefore ends
# `..., client, cloudflare`, and this count is the only thing deciding which entry becomes the key.
# At 1 the key is Cloudflare's edge, which rotates between requests, so a limit that should count a
# visitor's eleventh attempt counts roughly one in forty — measured on the deployed API, written up
# in the runbook, and pinned by a test. At 3 an attacker's own forged entry becomes the key, which is
# a bypass. Both directions are failures; this has to match the real topology rather than err.
# `prod.py` sets it to 2, and `render.yaml` sets it explicitly for the one host.
NINJA_NUM_PROXIES = env.int("NINJA_NUM_PROXIES", default=0)

# The throttle store. Ninja's throttles keep a rolling window of request timestamps in Django's
# default cache, which is a per-process, in-memory dictionary: the limits are therefore per process
# and reset on deploy. That is correct for how this app runs (one uvicorn process, see compose.yml
# and the Render start command) and wrong the moment there is more than one worker, because each
# would allow the full rate on its own. Point this at a shared backend — Render Key Value, or
# `django.core.cache.backends.db.DatabaseCache` if no extra service is wanted — before scaling out.
CACHES = {
    "default": {
        "BACKEND": env("CACHE_BACKEND", default="django.core.cache.backends.locmem.LocMemCache"),
        "LOCATION": env("CACHE_LOCATION", default="lysheim-throttle"),
    }
}

MIDDLEWARE = [
    "core.middleware.RequestIDMiddleware",
    # Above `CorsMiddleware` on purpose: that one answers a preflight itself and never reaches a
    # view, so a middleware below it would leave those responses unhardened. This one only decorates
    # whatever comes back, which is also why it has no opinion about the request.
    "core.middleware.ContentSecurityPolicyMiddleware",
    # The console's sign-in is a plain Django view, so Ninja's throttles cannot reach it and this is
    # what stands in front of it (`SEC-FIND-1.7`). Below the CSP middleware so a `429` still carries
    # the header, and above the CORS one so a preflight is not counted against anybody.
    "accounts.middleware.AdminLoginThrottleMiddleware",
    # Answers the browser's preflight itself and adds the CORS headers to every response, so it has
    # to sit above anything that could answer first — `CommonMiddleware` most of all.
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    # The admin's forms are the only thing in this backend that leans on Django's CSRF protection:
    # every `django-ninja` operation is exempted at the view, so this adds no check to an API
    # request. The API's own cookie surface (`/auth/refresh`) keeps its origin guard (`ADR-0009`).
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    # The admin is the one page here that renders server-side HTML a person signs into, so it is
    # the one worth refusing to frame; API responses are JSON and unaffected.
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            # Django admin's own pages read all three (its sidebar, its user menu, its messages).
            # Nothing in the storefront renders through a Django template — the frontend is Next.js
            # — so these cost the API nothing.
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
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

# Cross-origin access for the decoupled frontend (`ADR-0011`: the web app on Vercel, the API on
# Render). This allow-list is the only thing that decides who may call the API from a browser, and it
# is deliberately the same list `accounts/api.py` consults for the refresh origin guard, so the two
# cannot drift apart. Empty by default: a deployment that forgets to set it refuses cross-origin
# calls, which is the safe direction to fail in.
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])

# The refresh token travels in a cookie, so the browser has to be permitted to send credentials
# cross-origin. That is only safe *because* the origins above are an explicit allow-list — the
# package refuses to combine credentials with a wildcard, and a wildcard would defeat the origin
# guard on `/auth/refresh` at the same time.
CORS_ALLOW_CREDENTIALS = True

# A response header is invisible to JavaScript unless CORS says otherwise, and the correlation id is
# the one response header the web app has to read: it is how an error a shopper saw is matched to the
# log line that explains it (`NFR-5`, and the envelope in `API.md` section 3 carries the same value).
# `RUNBOOK.md` and the browser's own network tab would otherwise disagree about an id the server has
# been emitting all along — the "ids across API and web" half that is easy to leave half-done.
CORS_EXPOSE_HEADERS = [REQUEST_ID_HEADER]

# The `Content-Security-Policy` the API answers with (`SEC-FIND-1.4`, `SECURITY-BASELINE.md` section
# 6). Declared here rather than in the middleware because it is policy, in the same sense the throttle
# rates are (`ADR-0011`), and because the baseline's own list is the specification it has to match.
# The three directives beyond the baseline's are the cheap ones that close a real gap each: `base-uri`
# stops an injected `<base>` from re-pointing every relative URL on the page, `frame-ancestors` is
# what replaced `X-Frame-Options` for browsers that ignore the old header, and `form-action` stops a
# form on a page we served from posting an address somewhere else.
CONTENT_SECURITY_POLICY = "; ".join(
    [
        "default-src 'self'",
        "img-src 'self' data:",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
    ]
)

# The operator console cannot live under the policy above. Django's own admin templates carry inline
# `<script>` and `style` attributes, so `'unsafe-inline'` is the difference between a console that
# works and one that renders unstyled and half-dead — a broken console being the failure mode nobody
# forgives. Every origin restriction that matters is kept: nothing is allowed to load from anywhere
# but this host, and nothing may frame the console at all.
CONTENT_SECURITY_POLICY_ADMIN = "; ".join(
    [
        CONTENT_SECURITY_POLICY,
        "style-src 'self' 'unsafe-inline'",
        "script-src 'self' 'unsafe-inline'",
    ]
)

# Which payment adapter is in force (`ADR-0010`). Configuration, not code: a real provider is a
# second adapter in `payments/providers.py` plus a new value here, with no change in `orders`. The
# default is the mock so a bare checkout runs, and `prod.py` reads the same variable from the
# environment rather than hard-coding a provider.
PAYMENT_PROVIDER = env("PAYMENT_PROVIDER", default="mock")

# Background work runs on Django's built-in Tasks framework (`ADR-0006`). Django 6 ships only the
# `immediate` and `dummy` backends, so v1's default runs a task in the calling process — no broker,
# no worker process to pay for, and the enqueue still goes through the same `Task` object a
# worker-backed backend would. Pointing this at one later is a value here, not a code change.
TASKS = {
    "default": {
        "BACKEND": env(
            "DJANGO_TASK_BACKEND", default="django.tasks.backends.immediate.ImmediateBackend"
        ),
    }
}

# Email goes through Django's mail API, out of a transport that sends nothing — the mock-first spirit
# of `ADR-0010` applied to post: `locmem` collects messages in `django.core.mail.outbox` for dev and
# tests, so nothing reaches an inbox and nothing tries to reach localhost:25 either. Configured as a
# mailer rather than through `EMAIL_BACKEND`, which Django 6.1 deprecates (removed in 2028).
MAILERS = {
    "default": {
        "BACKEND": env(
            "DJANGO_MAILER_BACKEND", default="django.core.mail.backends.locmem.EmailBackend"
        ),
    }
}
DEFAULT_FROM_EMAIL = env("DJANGO_DEFAULT_FROM_EMAIL", default="LYSHEIM <no-reply@lysheim.example>")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"json": {"()": "core.logging.JsonFormatter"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "json"}},
    "root": {"handlers": ["console"], "level": env("DJANGO_LOG_LEVEL", default="INFO")},
}
