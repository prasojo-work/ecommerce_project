"""Seeder discovery for `manage.py seed`.

An app contributes seed steps by defining a `seeders` module that exports `STEPS`, a tuple of
`SeedStep`. `discover()` collects them.

Discovery reads the `STEPS` attribute from each module rather than relying on registration as an
import side effect. That matters: Python caches imported modules, so a registry mutated at import
time silently contributes nothing on a second pass — which is exactly what happens between tests,
and would have made `manage.py seed` a no-op with no error.
"""

from collections.abc import Callable
from dataclasses import dataclass
from importlib import import_module

from django.apps import apps


@dataclass(frozen=True)
class SeedStep:
    """One idempotent unit of seeding."""

    name: str
    run: Callable[[], None]
    clear: Callable[[], None] | None = None


def discover() -> tuple[SeedStep, ...]:
    """The steps contributed by installed apps, in `INSTALLED_APPS` order.

    Apps without a `seeders` module are skipped.
    """
    found: list[SeedStep] = []
    for config in apps.get_app_configs():
        try:
            module = import_module(f"{config.name}.seeders")
        except ModuleNotFoundError:
            continue
        found.extend(getattr(module, "STEPS", ()))
    return tuple(found)
