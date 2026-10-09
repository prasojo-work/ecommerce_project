import os

import pytest

from config.env import configure_settings


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
