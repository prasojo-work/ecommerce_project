"""The customer's address book (`API.md` section 8, `SCOPE.md` `US-2.5`).

Two rules are worth stating, because both are held by the shape of the code rather than by asking
people to remember them.

**Every row is reached through the caller's own scope.** Nothing here fetches an address by primary
key and then checks who owns it: the owner is part of the query, so an address belonging to somebody
else is simply not found and there is no branch in which the check can be forgotten. That is
`QA-C31`'s broken-object-level-authorization failure, and it is why the queries read
`Address.objects.filter(user=...)` rather than `user.addresses` — the reverse accessor is invisible
to `basedpyright`, which is the limitation `ADR-0014` records.

**A user who has any address has exactly one default.** `DATA-MODEL.md` gives the database a partial
unique index enforcing *at most one*; these endpoints hold the stronger rule so that checkout can
pick an address without asking which of several defaults won.
"""

from __future__ import annotations

from django.db import transaction
from ninja import Router, Status
from ninja.errors import HttpError

from accounts.auth import AuthenticatedRequest, auth
from accounts.models import Address, User
from accounts.schemas import AddressCreateSchema, AddressSchema, AddressUpdateSchema
from accounts.throttling import AuthenticatedRateThrottle

router = Router(tags=["accounts"])

NO_SUCH_ADDRESS = "No such address."

NOT_THE_DEFAULT = "An address must be the default. Set another address as the default instead."


def _addresses(user: User) -> list[Address]:
    """The caller's addresses, default first then oldest first — the model's own ordering."""
    return list(Address.objects.filter(user=user))


def _own_address(user: User, address_id: int) -> Address:
    """The caller's address with this id, or a `404`.

    `404` rather than `403` deliberately: `403` would confirm that the id exists, which is exactly
    what an attempt to enumerate other people's addresses is trying to learn.
    """
    address = Address.objects.filter(user=user, pk=address_id).first()
    if address is None:
        raise HttpError(404, NO_SUCH_ADDRESS)
    return address


def _clear_default(user: User, *, keep: Address | None = None) -> None:
    """Unset the default on every one of the caller's rows except `keep`.

    The partial unique index refuses two rows marked default even for an instant, so this has to run
    before the new default is written — which is why every caller below sits in a transaction.
    """
    rows = Address.objects.filter(user=user, is_default=True)
    if keep is not None:
        rows = rows.exclude(pk=keep.pk)
    rows.update(is_default=False)


@router.get(
    "",
    response=list[AddressSchema],
    auth=auth,
    throttle=[AuthenticatedRateThrottle()],
    summary="List addresses",
)
def list_addresses(request: AuthenticatedRequest) -> list[Address]:
    """`US-2.5`."""
    return _addresses(request.auth)


@router.post(
    "",
    response={201: AddressSchema},
    auth=auth,
    throttle=[AuthenticatedRateThrottle()],
    summary="Add an address",
)
def create_address(request: AuthenticatedRequest, payload: AddressCreateSchema) -> Status[Address]:
    """The first address becomes the default whether or not the client asked for it.

    An account whose only address is not the default is a state checkout would have to special-case
    for no benefit, so it is not reachable.
    """
    user = request.auth
    is_default = payload.is_default or not Address.objects.filter(user=user).exists()
    fields = payload.model_dump(exclude={"is_default"})

    with transaction.atomic():
        if is_default:
            _clear_default(user)
        address = Address.objects.create(user=user, is_default=is_default, **fields)
    return Status(201, address)


@router.patch(
    "/{address_id}",
    response=AddressSchema,
    auth=auth,
    throttle=[AuthenticatedRateThrottle()],
    summary="Update an address",
)
def update_address(
    request: AuthenticatedRequest, address_id: int, payload: AddressUpdateSchema
) -> Address:
    """`US-2.5`. Only the fields present in the body are touched."""
    user = request.auth
    changes = payload.model_dump(exclude_unset=True)

    with transaction.atomic():
        address = _own_address(user, address_id)
        if changes.get("is_default") is False and address.is_default:
            # Refused rather than ignored: silently keeping a value the client asked to change is
            # worse than saying no, and honouring it would leave the account with addresses and no
            # default to check out with. `409` rather than `400`: the body is well-formed and it is
            # the state of the resource that refuses it. `400` is what the frontend maps onto form
            # fields, and this is not a field error.
            raise HttpError(409, NOT_THE_DEFAULT)

        for field, value in changes.items():
            setattr(address, field, value)
        if address.is_default:
            _clear_default(user, keep=address)
        address.save(update_fields=[*changes, "updated_at"])

    return address


@router.delete(
    "/{address_id}",
    response={204: None},
    auth=auth,
    throttle=[AuthenticatedRateThrottle()],
    summary="Remove an address",
)
def delete_address(request: AuthenticatedRequest, address_id: int) -> Status[None]:
    """`US-2.5`.

    Deleting the default promotes the oldest survivor, so the account keeps exactly one default for
    as long as it has any address at all — the same invariant the other endpoints hold.
    """
    user = request.auth

    with transaction.atomic():
        address = _own_address(user, address_id)
        was_default = address.is_default
        address.delete()
        if was_default:
            replacement = Address.objects.filter(user=user).order_by("id").first()
            if replacement is not None:
                replacement.is_default = True
                replacement.save(update_fields=["is_default", "updated_at"])

    return Status(204, None)
