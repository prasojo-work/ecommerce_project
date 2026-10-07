from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from django.conf import settings

from accounts.models import RefreshToken, User

ALGORITHM = "HS256"


def _encode(user_id: int, token_type: str, ttl_seconds: int) -> tuple[str, str, datetime]:
    issued_at = datetime.now(tz=UTC)
    expires_at = issued_at + timedelta(seconds=ttl_seconds)
    jti = str(uuid.uuid4())
    payload = {
        "sub": str(user_id),
        "type": token_type,
        "jti": jti,
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)
    return token, jti, expires_at


def issue_access_token(user: User) -> str:
    token, _, _ = _encode(user.id, "access", settings.ACCESS_TOKEN_TTL_SECONDS)
    return token


def issue_refresh_token(user: User) -> str:
    token, jti, expires_at = _encode(user.id, "refresh", settings.REFRESH_TOKEN_TTL_SECONDS)
    RefreshToken.objects.create(user=user, jti=jti, expires_at=expires_at)
    return token


def decode_token(token: str, expected_type: str) -> dict[str, Any] | None:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None
    if payload.get("type") != expected_type:
        return None
    return payload
