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
