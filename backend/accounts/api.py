from __future__ import annotations

from typing import Any

from django.conf import settings
from django.contrib.auth import authenticate
from django.http import HttpResponse
from django.utils import timezone
from ninja import Router, Status
from ninja.errors import HttpError

from accounts.auth import jwt_auth
from accounts.models import Address, RefreshToken, User
from accounts.schemas import (
    AccessTokenOut,
    AddressIn,
    AddressOut,
    AddressPatch,
    LoginIn,
    RegisterIn,
    UserOut,
)
from accounts.tokens import decode_token, issue_access_token, issue_refresh_token

router = Router(tags=["accounts"])

REFRESH_COOKIE_PATH = "/api/v1/auth"


def _set_refresh_cookie(response: HttpResponse, token: str) -> None:
    response.set_cookie(
        settings.REFRESH_COOKIE_NAME,
        token,
        max_age=settings.REFRESH_TOKEN_TTL_SECONDS,
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite="Lax",
        path=REFRESH_COOKIE_PATH,
    )


def _clear_refresh_cookie(response: HttpResponse) -> None:
    response.delete_cookie(settings.REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH)


def _access_token_out(user: User) -> AccessTokenOut:
    return AccessTokenOut(
        access_token=issue_access_token(user),
        expires_in=settings.ACCESS_TOKEN_TTL_SECONDS,
    )


@router.post("/auth/register", response={201: AccessTokenOut})
def register(
    request: Any, payload: RegisterIn, response: HttpResponse
) -> Status[AccessTokenOut]:
    if User.objects.filter(email__iexact=payload.email).exists():
        raise HttpError(400, "An account with this email already exists.")
    user = User.objects.create_user(
        email=payload.email, password=payload.password, full_name=payload.full_name
    )
    _set_refresh_cookie(response, issue_refresh_token(user))
    return Status(201, _access_token_out(user))


@router.post("/auth/login", response=AccessTokenOut)
def login(request: Any, payload: LoginIn, response: HttpResponse) -> AccessTokenOut:
    user = authenticate(request, username=payload.email, password=payload.password)
    if user is None:
        raise HttpError(401, "Invalid email or password.")
    _set_refresh_cookie(response, issue_refresh_token(user))
    return _access_token_out(user)


@router.post("/auth/refresh", response=AccessTokenOut)
def refresh(request: Any, response: HttpResponse) -> AccessTokenOut:
    raw = request.COOKIES.get(settings.REFRESH_COOKIE_NAME)
    payload = decode_token(raw, "refresh") if raw else None
    if payload is None:
        raise HttpError(401, "A valid refresh token is required.")
    stored = RefreshToken.objects.filter(jti=payload["jti"], revoked_at__isnull=True).first()
    user = User.objects.filter(pk=payload["sub"], is_active=True).first()
    if stored is None or user is None:
        raise HttpError(401, "This refresh token is no longer valid.")
    stored.revoked_at = timezone.now()
    stored.save(update_fields=["revoked_at"])
    _set_refresh_cookie(response, issue_refresh_token(user))
    return _access_token_out(user)


@router.post("/auth/logout", response={204: None})
def logout(request: Any, response: HttpResponse) -> Status[None]:
    raw = request.COOKIES.get(settings.REFRESH_COOKIE_NAME)
    payload = decode_token(raw, "refresh") if raw else None
    if payload is not None:
        RefreshToken.objects.filter(jti=payload["jti"], revoked_at__isnull=True).update(
            revoked_at=timezone.now()
        )
    _clear_refresh_cookie(response)
    return Status(204, None)


@router.get("/auth/me", auth=jwt_auth, response=UserOut)
def me(request: Any) -> UserOut:
    user = request.auth
    return UserOut(id=user.id, email=user.email, full_name=user.full_name)


def _address_out(address: Address) -> AddressOut:
    return AddressOut(
        id=address.id,
        recipient=address.recipient,
        phone=address.phone,
        line1=address.line1,
        line2=address.line2,
        city=address.city,
        province=address.province,
        postal_code=address.postal_code,
        country=address.country,
        is_default=address.is_default,
    )


def _owned_address(request: Any, address_id: int) -> Address:
    address = Address.objects.filter(pk=address_id, user=request.auth).first()
    if address is None:
        raise HttpError(404, "Address not found.")
    return address


@router.get("/addresses", auth=jwt_auth, response=list[AddressOut])
def list_addresses(request: Any) -> list[AddressOut]:
    addresses = Address.objects.filter(user=request.auth)
    return [_address_out(address) for address in addresses]


@router.post("/addresses", auth=jwt_auth, response={201: AddressOut})
def create_address(request: Any, payload: AddressIn) -> Status[AddressOut]:
    address = Address.objects.create(user=request.auth, **payload.model_dump())
    return Status(201, _address_out(address))


@router.get("/addresses/{address_id}", auth=jwt_auth, response=AddressOut)
def get_address(request: Any, address_id: int) -> AddressOut:
    return _address_out(_owned_address(request, address_id))


@router.patch("/addresses/{address_id}", auth=jwt_auth, response=AddressOut)
def update_address(request: Any, address_id: int, payload: AddressPatch) -> AddressOut:
    address = _owned_address(request, address_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(address, field, value)
    address.save()
    return _address_out(address)


@router.delete("/addresses/{address_id}", auth=jwt_auth, response={204: None})
def delete_address(request: Any, address_id: int) -> Status[None]:
    _owned_address(request, address_id).delete()
    return Status(204, None)
