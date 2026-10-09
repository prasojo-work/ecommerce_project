"""Select the Django settings module from the environment.

`DJANGO_ENV` picks the module under `config.settings` (`dev` or `prod`). An explicit
`DJANGO_SETTINGS_MODULE` always wins, so tooling such as pytest and basedpyright can keep
pinning its own module.
"""

import os

DEFAULT_ENV = "dev"
VALID_ENVS = ("dev", "prod")


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
