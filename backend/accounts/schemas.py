"""Request and response schemas for the auth surface: `API.md` section 2 and section 8."""

from ninja import Schema
from pydantic import Field


class RegisterSchema(Schema):
    email: str
    password: str
    display_name: str = ""


class LoginSchema(Schema):
    email: str
    password: str


class UserSchema(Schema):
    """The account as a client sees it. Never the password, never a token."""

    id: int
    email: str
    display_name: str
    is_staff: bool


class TokenSchema(Schema):
    """The sign-in payload.

    The refresh token is deliberately absent. `ADR-0009` delivers it only as an httpOnly cookie so
    that no script — including a compromised one — can read it, and `API.md` section 2 documents the
    access token as the only token in the body.
    """

    access_token: str
    # A public scheme name, not a credential; `S105` fires on the word in the field name.
    token_type: str = "Bearer"  # noqa: S105
    expires_in: int
    user: UserSchema


class ProfileUpdateSchema(Schema):
    """`US-2.4`. An absent field means "leave it unchanged", because a `PATCH` sends only changes."""

    display_name: str | None = Field(default=None, max_length=120)


class AddressSchema(Schema):
    """A stored address, as a client sees it (`API.md` section 8)."""

    id: int
    label: str
    recipient: str
    line1: str
    line2: str
    city: str
    region: str
    postal_code: str
    country: str
    phone: str
    is_default: bool


class AddressCreateSchema(Schema):
    """A new address. `label`, `line2`, `region` and `phone` are optional, as the model has them.

    The lengths are the model's, repeated here so an over-long field is a `400` naming the field
    rather than a database error on PostgreSQL and a silent pass on SQLite — the difference `M1.2`
    found the hard way. The required fields also carry a floor of one character: the model declares
    them non-blank, and nothing in the database refuses `recipient = ""`, so without this an address
    checkout could not use would be stored happily.
    """

    label: str = Field(default="", max_length=60)
    recipient: str = Field(min_length=1, max_length=120)
    line1: str = Field(min_length=1, max_length=120)
    line2: str = Field(default="", max_length=120)
    city: str = Field(min_length=1, max_length=120)
    region: str = Field(default="", max_length=120)
    postal_code: str = Field(min_length=1, max_length=32)
    country: str = Field(min_length=2, max_length=2)
    phone: str = Field(default="", max_length=32)
    is_default: bool = False


class AddressUpdateSchema(Schema):
    """Every field optional: a `PATCH` sends only what changed (`API.md` section 8)."""

    label: str | None = Field(default=None, max_length=60)
    recipient: str | None = Field(default=None, min_length=1, max_length=120)
    line1: str | None = Field(default=None, min_length=1, max_length=120)
    line2: str | None = Field(default=None, max_length=120)
    city: str | None = Field(default=None, min_length=1, max_length=120)
    region: str | None = Field(default=None, max_length=120)
    postal_code: str | None = Field(default=None, min_length=1, max_length=32)
    country: str | None = Field(default=None, min_length=2, max_length=2)
    phone: str | None = Field(default=None, max_length=32)
    is_default: bool | None = None
