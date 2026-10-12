"""The orders context's public interface (`ARCHITECTURE.md` section 4).

The models hold the shape and the rules; this module holds the acts. Order creation (`M4.3`) will
land here beside the transition, because both are the same kind of thing — an operation that has to
validate, write more than one row, and leave nothing half-done if it fails.

Nothing calls this yet: `M4.1` is the model and its guard. The endpoints that will (`M4.3`'s
checkout, `M5.5`'s operator console) go through here rather than assigning `order.status`, which is
what makes `ALLOWED_TRANSITIONS` a rule instead of a suggestion.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import transaction

from orders.models import ALLOWED_TRANSITIONS, Order, OrderEvent

if TYPE_CHECKING:
    from accounts.models import User


class InvalidTransition(RuntimeError):
    """An order was asked to reach a status it cannot reach from where it is."""


@transaction.atomic
def transition_order(
    order: Order, to_status: str, *, actor: User | None = None, note: str = ""
) -> Order:
    """Move `order` to `to_status` and record who did it (`US-5.5`, `DATA-MODEL.md` section 3).

    The guard and the record are one transaction on purpose. An audit trail written in a second step
    is an audit trail with a gap in it whenever the second step fails, and a gap is worse than no
    trail because it still looks complete.

    The row is locked for the duration. Two operators reading `paid` at the same moment would both
    find `shipped` reachable and both write an event claiming to have moved the order from the same
    place — one transition, two records of it.

    Raises `InvalidTransition` rather than returning a flag: every caller so far is answering a
    request that should become a `409`, and an exception is what carries that decision outward
    without every layer in between having to pass it along.
    """
    locked = Order.objects.select_for_update().get(pk=order.pk)

    from_status = locked.status
    if to_status not in ALLOWED_TRANSITIONS[from_status]:
        raise InvalidTransition(f"An order that is {from_status} cannot become {to_status}.")

    locked.status = to_status
    # `updated_at` is `auto_now`, so it only moves if it is named here.
    locked.save(update_fields=["status", "updated_at"])

    OrderEvent.objects.create(
        order=locked, from_status=from_status, to_status=to_status, actor=actor, note=note
    )

    return locked
