"""Off-request work for the orders context (`ADR-0006`, `ARCHITECTURE.md` section 6).

One job so far: the confirmation email. It is a `Task` rather than a call made inline because the
customer has already paid by the time it runs, and a slow mail transport should not be something they
wait on.

The task takes an **id**, not the order. Whatever crosses a queue boundary has to be serialisable and
the row it names has to be re-read on the other side, so an object would work only for the backend
that happens to run in-process — which is exactly the accident this is written to avoid.
"""

from __future__ import annotations

from django.conf import settings
from django.core.mail import send_mail
from django.tasks import task
from django.template.loader import render_to_string

from orders.models import Order, OrderItem

CONFIRMATION_TEMPLATE = "orders/confirmation_email.txt"


def _money(amount_cents: int, currency: str) -> str:
    """`12900` as `USD 129.00` — integer arithmetic, because money is never a float here."""
    return f"{currency} {amount_cents // 100}.{amount_cents % 100:02d}"


@task
def send_order_confirmation(order_id: int) -> int:
    """Email the receipt for `order_id` and answer how many messages went out.

    Formatting happens here rather than in the template because a `.txt` receipt is presentation and
    the arithmetic is not; the template receives strings and holds none of the project's rules about
    money.
    """
    order = Order.objects.get(pk=order_id)
    currency = order.currency

    lines = [
        {
            "product_name": item.product_name,
            "variant_name": item.variant_name,
            "quantity": item.quantity,
            "unit_price": _money(item.unit_price_cents, currency),
            "line_total": _money(item.line_total_cents, currency),
        }
        for item in OrderItem.objects.filter(order=order).order_by("id")
    ]

    # Blank lines dropped rather than printed as gaps: `line2` and `region` are optional, and an
    # address with a hole in the middle of it reads as a mistake.
    address = [
        part
        for part in (
            order.shipping_recipient,
            order.shipping_line1,
            order.shipping_line2,
            order.shipping_city,
            order.shipping_region,
            order.shipping_postal_code,
            order.shipping_country,
        )
        if part
    ]

    body = render_to_string(
        CONFIRMATION_TEMPLATE,
        {
            "number": order.number,
            "lines": lines,
            "subtotal": _money(order.subtotal_cents, currency),
            "shipping": _money(order.shipping_cents, currency),
            "total": _money(order.total_cents, currency),
            "address": address,
        },
    )

    return send_mail(
        subject=f"Your LYSHEIM order {order.number}",
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.email],
        fail_silently=False,
    )
