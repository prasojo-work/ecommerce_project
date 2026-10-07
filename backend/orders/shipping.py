"""Shipping options for checkout.

`DATA-MODEL.md` models shipping as a single monetary column (`order.shipping_cost`)
and `ARCHITECTURE.md` §4 assigns "shipping" to the `orders` app, so the options are
defined in code rather than persisted in a table. The free-delivery threshold
mirrors the customer-facing promise in `UX.md` ("Free delivery over Rp 500.000").
"""

from __future__ import annotations

from dataclasses import dataclass

FREE_SHIPPING_THRESHOLD = 500_000
DEFAULT_SHIPPING_CODE = "standard"


@dataclass(frozen=True)
class ShippingOption:
    code: str
    name: str
    cost: int
    eta: str


SHIPPING_OPTIONS: tuple[ShippingOption, ...] = (
    ShippingOption(code="standard", name="Standard delivery", cost=25_000, eta="3–5 days"),
    ShippingOption(code="express", name="Express delivery", cost=60_000, eta="1–2 days"),
)


def get_option(code: str) -> ShippingOption | None:
    return next((option for option in SHIPPING_OPTIONS if option.code == code), None)


def cost_for(option: ShippingOption, subtotal: int) -> int:
    """Standard delivery is free once the basket clears the threshold."""
    if option.code == DEFAULT_SHIPPING_CODE and subtotal >= FREE_SHIPPING_THRESHOLD:
        return 0
    return option.cost


def options_for(subtotal: int) -> list[tuple[ShippingOption, int]]:
    return [(option, cost_for(option, subtotal)) for option in SHIPPING_OPTIONS]
