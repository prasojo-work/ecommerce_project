from __future__ import annotations

from typing import Any

from ninja.security import HttpBearer

from accounts.models import User
from accounts.tokens import decode_token


class JWTAuth(HttpBearer):
    def authenticate(self, request: Any, token: str) -> User | None:
        payload = decode_token(token, "access")
        if payload is None:
            return None
        return User.objects.filter(pk=payload.get("sub"), is_active=True).first()
