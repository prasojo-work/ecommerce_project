from __future__ import annotations

from ninja import Schema
from pydantic import EmailStr


class RegisterIn(Schema):
    email: EmailStr
    password: str
    full_name: str = ""


class LoginIn(Schema):
    email: EmailStr
    password: str


class UserOut(Schema):
    id: int
    email: str
    full_name: str


class AccessTokenOut(Schema):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int


class AddressIn(Schema):
    recipient: str
    phone: str
    line1: str
    line2: str = ""
    city: str
    province: str
    postal_code: str
    country: str = "ID"
    is_default: bool = False


class AddressPatch(Schema):
    recipient: str | None = None
    phone: str | None = None
    line1: str | None = None
    line2: str | None = None
    city: str | None = None
    province: str | None = None
    postal_code: str | None = None
    country: str | None = None
    is_default: bool | None = None


class AddressOut(Schema):
    id: int
    recipient: str
    phone: str
    line1: str
    line2: str
    city: str
    province: str
    postal_code: str
    country: str
    is_default: bool
