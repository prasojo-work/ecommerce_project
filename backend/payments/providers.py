"""Adapter selection (`ADR-0010`).

`PAYMENT_PROVIDER` is configuration, not code (`ARCHITECTURE.md` section 1, principle 4). Exactly
one adapter exists in v1, so this is a lookup with a clear failure rather than a registry: an unknown
value is a misconfiguration that should stop the request, not fall back to pretending.
"""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from payments.gateway import PaymentGateway
from payments.mock import MockGateway

#: The value `PAYMENT_PROVIDER` takes for the only v1 adapter.
MOCK = "mock"


def get_gateway() -> PaymentGateway:
    """The adapter named by `PAYMENT_PROVIDER`."""
    provider = settings.PAYMENT_PROVIDER
    if provider == MOCK:
        return MockGateway()
    raise ImproperlyConfigured(
        f"PAYMENT_PROVIDER is '{provider}', which names no adapter. Add one in "
        "payments/providers.py and select it here."
    )
