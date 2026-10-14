import os

import pytest
from django.core.exceptions import ImproperlyConfigured

from config.env import INSECURE_DEVELOPMENT_KEY, configure_settings, ensure_production_secret_key


def test_explicit_settings_module_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "config.settings.prod")
    monkeypatch.setenv("DJANGO_ENV", "dev")

    assert configure_settings() == "config.settings.prod"


def test_django_env_selects_module(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DJANGO_SETTINGS_MODULE", raising=False)
    monkeypatch.setenv("DJANGO_ENV", "prod")

    assert configure_settings() == "config.settings.prod"
    assert os.environ["DJANGO_SETTINGS_MODULE"] == "config.settings.prod"


def test_falls_back_to_dev(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DJANGO_SETTINGS_MODULE", raising=False)
    monkeypatch.delenv("DJANGO_ENV", raising=False)

    assert configure_settings() == "config.settings.dev"


def test_unknown_django_env_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DJANGO_SETTINGS_MODULE", raising=False)
    monkeypatch.setenv("DJANGO_ENV", "staging")

    with pytest.raises(RuntimeError, match="DJANGO_ENV"):
        configure_settings()


def test_production_refuses_the_development_secret_key() -> None:
    """`SEC-FIND-1.5`: the value checked in to this repository is not one a deployment may serve on.

    Asserted here rather than by importing `config.settings.prod`, because in a test environment with
    `DJANGO_SECRET_KEY` unset the import is the very thing that raises — which makes the obvious test
    ("does importing prod fail?") pass for the wrong reason, and fail outright on a machine whose
    `.env` sets a real key.
    """
    with pytest.raises(ImproperlyConfigured, match="DJANGO_SECRET_KEY"):
        ensure_production_secret_key(INSECURE_DEVELOPMENT_KEY)


def test_production_accepts_a_configured_secret_key() -> None:
    """The other direction, so the guard is a judgement about the value rather than a refusal to run."""
    ensure_production_secret_key("6f1c0b2e4a7d9f3b5c8e0a1d2f4b6c8e9a0d1f3b5c7e9a1b2d4f6c8e0a1b3d5f")
