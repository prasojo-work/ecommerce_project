"""Shipping methods, simulated (`SCOPE.md` `US-4.2`, `ADR-0010`).

v1 integrates no carrier — `SCOPE.md` section 5 puts real logistics out of scope — so the methods
below are a fixed, published set of flat rates rather than a price from anybody. They live in one
place so the catalogue is a value to change rather than a number buried in the endpoint, the shape
`PAYMENT_PROVIDER=mock` gives payments (`ADR-0010`).

The rates are address-independent on purpose. This module is the seam a real carrier would slot
into, and a rate that ignored the address it was handed would only be pretending otherwise — so
the flatness is stated here rather than hidden behind a signature that looks like it calculated
something. The quote still takes an address, because `US-4.1`'s validation belongs there and a real
rate would need it.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ShippingMethod:
    """One selectable shipping option."""

    code: str
    name: str
    description: str
    price_cents: int


SHIPPING_METHODS: tuple[ShippingMethod, ...] = (
    ShippingMethod(
        code="standard",
        name="Standard delivery",
        description="Arrives in 5-7 business days.",
        price_cents=1900,
    ),
    ShippingMethod(
        code="express",
        name="Express delivery",
        description="Arrives in 2-3 business days.",
        price_cents=4900,
    ),
)

# The option checkout preselects. Named rather than positional, so reordering the tuple above
# cannot silently change which method that is.
DEFAULT_METHOD_CODE = "standard"


def get_method(code: str) -> ShippingMethod | None:
    """The method with this code, or `None` when it does not exist."""
    return next((method for method in SHIPPING_METHODS if method.code == code), None)
