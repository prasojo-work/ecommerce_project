"""A deploy that copies `.env.example` verbatim must not start.

The placeholder key is committed, so booting on it would let anyone forge an
access token or sign a session cookie. See `SEC-FIND-1.1` in
`docs/04-delivery/SECURITY-REVIEW.md`.
"""

import pytest
from django.core.exceptions import ImproperlyConfigured

from config.settings import require_real_secret_key


def test_placeholder_secret_key_is_refused():
    with pytest.raises(ImproperlyConfigured):
        require_real_secret_key("change-me")


def test_a_real_secret_key_passes_through():
    real = "s3cr3t-value-from-the-environment"

    assert require_real_secret_key(real) == real
