"""Catalog read caching (`ADR-0013`).

Public catalog reads are the hot path — every listing render, every product page —
and they change only when an operator edits the catalog. They are the one thing
worth caching.

A write must be visible on the very next read, so every entry sits behind a
version token that a write bumps. Stale entries are then never looked up again and
expire unread, which keeps invalidation O(1) and backend-agnostic: no
`delete_pattern()`, which not every cache backend implements.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from uuid import uuid4

from django.core.cache import cache

# Backstop only. Writes invalidate immediately (`catalog/signals.py`), so this
# bounds the damage if a write path ever bypasses the ORM's signals — a bulk
# `QuerySet.update()`, say — rather than being the freshness mechanism.
CATALOG_CACHE_TTL_SECONDS = 300

_VERSION_KEY = "catalog:version"
_MISSING = object()


def _version() -> str:
    """The current cache generation. A write replaces it."""
    return cache.get_or_set(_VERSION_KEY, lambda: uuid4().hex, None)


def invalidate_catalog_cache() -> None:
    """Retire every cached catalog read by starting a new generation."""
    cache.delete(_VERSION_KEY)


def cached[T](key: str, build: Callable[[], T]) -> T:
    """Return `build()`'s result, from cache when one exists.

    `None` is a legitimate cached value (a slug that has no active product), so
    absence is tracked with a sentinel rather than a falsy check.
    """
    cache_key = f"catalog:{_version()}:{key}"
    found: Any = cache.get(cache_key, _MISSING)
    if found is _MISSING:
        found = build()
        cache.set(cache_key, found, CATALOG_CACHE_TTL_SECONDS)
    return found
