"""Access and refresh tokens: issuing, verification and rotation (`ADR-0009`).

The access token is a short-lived stateless JWT and is never stored. The refresh token is a JWT
too — `US-2.2` asks for a "JWT access + refresh pair" — but every one of them has a matching
`refresh_tokens` row keyed by its `jti`, because `ADR-0009` requires logout to invalidate it
server-side, which a signature alone cannot do.

A token is only accepted for the operation it was minted for: the two types are not
interchangeable, so an access token can never be traded for a new pair.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from accounts.models import RefreshToken, User

# `typ` distinguishes the two kinds of token. These are public discriminators, not secrets — `S105`
# fires on the word "token" in the name.
ACCESS_TOKEN_TYPE = "access"  # noqa: S105
REFRESH_TOKEN_TYPE = "refresh"  # noqa: S105

# `sub` and `typ` are required alongside the expiry, so a token minted by some other tool — or by
# an older revision of this one — is refused rather than half-understood.
REQUIRED_CLAIMS = ["exp", "iat", "sub", "typ"]

SESSION_UNKNOWN_MESSAGE = "That session is no longer valid. Sign in again."
SESSION_EXPIRED_MESSAGE = "That session has expired. Sign in again."
SESSION_REUSED_MESSAGE = "That session has ended. Sign in again."


class TokenError(Exception):
    """A token is missing, malformed, expired, revoked, or not valid for this operation."""


class _Replayed(Exception):
    """Internal: a rotated token's replacement has been spent, so a copy is in circulation.

    Carried out of the transaction as an exception rather than left as a flag inside it, because the
    sweep that follows has to happen *after* `atomic()` has rolled back — and a write made inside a
    block that is about to roll back is a write that does not survive.
    """

    def __init__(self, user: User) -> None:
        super().__init__(user.pk)
        self.user: User = user


@dataclass(frozen=True)
class TokenPair:
    """A freshly minted pair, plus what a client needs to reason about expiry."""

    access_token: str
    refresh_token: str
    access_expires_in: int
    refresh_expires_at: datetime


def _encode(
    subject: str, token_type: str, lifetime: timedelta, jti: uuid.UUID | None = None
) -> tuple[str, datetime]:
    issued_at = datetime.now(tz=UTC)
    expires_at = issued_at + lifetime
    claims: dict[str, Any] = {
        "sub": subject,
        "typ": token_type,
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    if jti is not None:
        claims["jti"] = str(jti)
    return jwt.encode(claims, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM), expires_at


def decode(token: str, expected_type: str) -> dict[str, Any]:
    """Verify a token's signature, expiry and type. Raises `TokenError` if any of them fails."""
    try:
        claims: dict[str, Any] = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            # Pinning the algorithm is what stops an `alg: none` forgery or an RS/HS confusion
            # attack: PyJWT will not infer it from the token's own header.
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": REQUIRED_CLAIMS},
        )
    except jwt.InvalidTokenError as exc:
        raise TokenError(SESSION_UNKNOWN_MESSAGE) from exc

    if claims["typ"] != expected_type:
        raise TokenError(SESSION_UNKNOWN_MESSAGE)
    return claims


def _issue_pair(user: User) -> tuple[TokenPair, RefreshToken]:
    """A fresh pair, and the row recording its refresh half, so a caller can link the two."""
    jti = uuid.uuid4()
    refresh_token, refresh_expires_at = _encode(
        str(user.pk),
        REFRESH_TOKEN_TYPE,
        timedelta(seconds=settings.REFRESH_TOKEN_TTL_SECONDS),
        jti=jti,
    )
    row = RefreshToken.objects.create(user=user, jti=jti, expires_at=refresh_expires_at)

    access_token, _ = _encode(
        str(user.pk),
        ACCESS_TOKEN_TYPE,
        timedelta(seconds=settings.ACCESS_TOKEN_TTL_SECONDS),
    )
    return (
        TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            access_expires_in=int(settings.ACCESS_TOKEN_TTL_SECONDS),
            refresh_expires_at=refresh_expires_at,
        ),
        row,
    )


def issue_tokens(user: User) -> TokenPair:
    """A fresh pair, with the refresh half recorded so that it can be revoked."""
    return _issue_pair(user)[0]


def resolve_access_token(token: str) -> User | None:
    """The active user a valid access token names, or `None` when it is not usable."""
    try:
        claims = decode(token, ACCESS_TOKEN_TYPE)
    except TokenError:
        return None
    return User.objects.filter(pk=claims["sub"], is_active=True).first()


def revoke(refresh_token: str) -> None:
    """Revoke one refresh token. Idempotent, so signing out always succeeds.

    A token that is unreadable, unknown or already revoked is a no-op rather than an error: the
    caller is signing out either way and the cookie is cleared regardless.
    """
    try:
        claims = decode(refresh_token, REFRESH_TOKEN_TYPE)
    except TokenError:
        return
    RefreshToken.objects.filter(jti=claims["jti"], revoked_at__isnull=True).update(
        revoked_at=timezone.now()
    )


def revoke_all(user: User) -> int:
    """Revoke every live refresh token for a user, returning how many were revoked."""
    return RefreshToken.objects.filter(user=user, revoked_at__isnull=True).update(
        revoked_at=timezone.now()
    )


def rotate(refresh_token: str) -> tuple[User, TokenPair]:
    """Trade a refresh token for a new pair, revoking the one presented (`US-2.3`).

    Reuse detection: presenting a token that is *already* revoked means a copy is in circulation,
    because the legitimate client would have moved on to the replacement. Every live token for that
    user is revoked — turning a stolen token into a detected event rather than a silent permanent
    session — and the request is refused. A token revoked by an ordinary sign-out reaches the same
    branch, which is conservative but harmless: everything is already revoked, so it is a no-op.

    One case is not a leak. A browser that navigates away while its refresh is in flight gets the
    cancellation instead of the new cookie, and the next page load presents the old token again; the
    replacement then went nowhere and nobody has ever held it. So while the replacement is unspent
    and no older than `REFRESH_ROTATION_GRACE_SECONDS`, the replay is read as that retry — the
    replacement is withdrawn, this token is pointed at its own successor, and a pair is issued. The
    grace is what keeps that from being a hole: a stolen token is only ever *spent* by its
    replacement being used, so a replay past the grace, or one whose replacement was spent, is a
    leak again and the sweep stands.

    The presented row is locked for the duration, so two concurrent refreshes with one token cannot
    both mint a session. SQLite ignores `SELECT ... FOR UPDATE`; Postgres honours it.
    """
    claims = decode(refresh_token, REFRESH_TOKEN_TYPE)
    now = timezone.now()
    grace = timedelta(seconds=settings.REFRESH_ROTATION_GRACE_SECONDS)

    try:
        with transaction.atomic():
            row = (
                RefreshToken.objects.select_for_update()
                .select_related("user")
                .filter(jti=claims["jti"])
                .first()
            )
            if row is None:
                raise TokenError(SESSION_UNKNOWN_MESSAGE)

            # Read as its own query rather than through `select_related`: a replacement is a nullable
            # FK, and Postgres refuses `FOR UPDATE` on the nullable side of the outer join that adds
            # (`NotSupportedError`). It is also only ever wanted for a dead row, so the live path —
            # every refresh that is not a replay — does not pay for it.
            replacement = (
                RefreshToken.objects.filter(replaces=row).first()
                if row.revoked_at is not None
                else None
            )
            retry = (
                replacement is not None
                and replacement.revoked_at is None
                and replacement.replaced_by_id is None
                and replacement.created_at > now - grace
            )

            if row.revoked_at is None:
                if row.expires_at <= now:
                    raise TokenError(SESSION_EXPIRED_MESSAGE)
                row.revoked_at = now
                row.save(update_fields=["revoked_at", "updated_at"])
            elif not retry:
                raise _Replayed(row.user)
            elif replacement is not None:
                # Withdrawn before a fresh pair supersedes it: nobody can have received it, but a
                # live token is a live session until it is revoked.
                replacement.revoked_at = now
                replacement.save(update_fields=["revoked_at", "updated_at"])

            # Pointed at the successor so a later replay can ask what became of the replacement
            # rather than only that there was one.
            pair, successor = _issue_pair(row.user)
            row.replaced_by = successor
            row.save(update_fields=["replaced_by"])
    except _Replayed as replayed:
        # Outside the transaction on purpose: revoking the whole family has to survive the rollback
        # the raise above triggered, and a write inside `atomic()` would go back with it.
        revoke_all(replayed.user)
        raise TokenError(SESSION_REUSED_MESSAGE) from None

    return row.user, pair
