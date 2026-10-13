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

# The balancer terminates TLS and forwards plain HTTP, so Django has to be told to believe
# `X-Forwarded-Proto`. Without this line `SECURE_SSL_REDIRECT` above sees an insecure connection on
# every single request — including one that arrived over HTTPS — and redirects to the HTTPS URL it is
# already serving: a loop, for every visitor and for the health check. Trusting the header is safe
# for the same reason `NINJA_NUM_PROXIES = 2` below is safe: the app is not reachable except through
# the balancer.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ...except for the health probe, which is not a browser and has nothing to upgrade to. Exempting it
# means the probe answers `200` whether it arrives over HTTP or HTTPS, so a redirect can never be the
# reason a deploy fails to come up.
SECURE_REDIRECT_EXEMPT = [r"^healthz$"]

# The API and the web app are different sites in production (Render and Vercel), so the refresh
# cookie has to be `SameSite=None` to survive the cross-site call — and browsers only accept
# `SameSite=None` together with `Secure` (`ADR-0009`).
REFRESH_COOKIE_SECURE = True
REFRESH_COOKIE_SAMESITE = "None"

# Two proxies, not one: Cloudflare's edge *and* Render's load balancer behind it, so the header the
# app reads ends `..., client, cloudflare` and the count has to skip both to land on the visitor.
# Getting this wrong is silent — it changes whose requests a limit counts, not whether it works —
# which is why the deployed API was measured rather than reasoned about. `base.py` has the numbers.
NINJA_NUM_PROXIES = env.int("NINJA_NUM_PROXIES", default=2)

# `base.py`'s mailer is `locmem`, which keeps every message it "sends" in `django.core.mail.outbox` —
# right for dev and tests, and wrong for a long-lived web process, where the list would grow with every
# order and never shrink. Production discards the message instead: the transport is mocked (`ADR-0010`)
# and until a real one exists there is nobody to hand the receipt to.
MAILERS = {"default": {"BACKEND": "django.core.mail.backends.dummy.EmailBackend"}}
