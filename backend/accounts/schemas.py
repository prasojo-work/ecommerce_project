"""Request and response schemas for the auth endpoints (`API.md` section 2)."""

from ninja import Schema


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
