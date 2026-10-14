"""Configuration guards, and selection of the settings module from the environment.

`DJANGO_ENV` picks the module under `config.settings` (`dev` or `prod`). An explicit
`DJANGO_SETTINGS_MODULE` always wins, so tooling such as pytest and basedpyright can keep
pinning its own module.
"""

import os

from django.core.exceptions import ImproperlyConfigured

DEFAULT_ENV = "dev"
VALID_ENVS = ("dev", "prod")

# The value `base.py` falls back to when `DJANGO_SECRET_KEY` is unset. Named rather than written out
# twice because two modules have to agree on it: `base.py` uses it as the default, and the guard
# below refuses to serve production on it (`SEC-FIND-1.5`).
INSECURE_DEVELOPMENT_KEY = "insecure-development-key-change-me"


def configure_settings() -> str:
    """Set `DJANGO_SETTINGS_MODULE` from `DJANGO_ENV`, unless it is already set.

    Returns the settings module now in effect.
    """
    current = os.environ.get("DJANGO_SETTINGS_MODULE")
    if current:
        return current

    name = os.environ.get("DJANGO_ENV", DEFAULT_ENV).strip().lower()
    if name not in VALID_ENVS:
        raise RuntimeError(f"DJANGO_ENV must be one of {', '.join(VALID_ENVS)}; got {name!r}.")

    module = f"config.settings.{name}"
    os.environ["DJANGO_SETTINGS_MODULE"] = module
    return module


def ensure_production_secret_key(secret_key: str) -> None:
    """Refuse to run production on the development key (`SEC-FIND-1.5`).

    The check lives here, taking the value as an argument, rather than inline in `prod.py`: a guard
    there could only be exercised by importing that module, and in a test environment with no
    `DJANGO_SECRET_KEY` set, the import is the very thing that raises. Handing it the value lets a
    test assert both directions — the default refuses, a real key is accepted — without a subprocess
    and without depending on whether `.env` happens to exist on the machine.

    Failing at import is the point. The alternative is a deployment that answers every request while
    signing tokens with a key published in this repository, and nothing about that looks wrong from
    the outside.
    """
    if secret_key == INSECURE_DEVELOPMENT_KEY:
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY must be set in production; refusing to serve with the "
            "development key from the repository."
        )
