"""Seeder registry for `manage.py seed`.

`M1.2` registers the catalog seeders here. Each step must be **idempotent**: running the command
twice must leave the database in the same state, because `manage.py seed` is expected to be safe
to re-run (see `docs/WORKING-AGREEMENT.md` section 1.7).

Steps run in registration order. `clear` is optional and exists for `--reset`, which removes the
seeded rows first so a demo can start from a known state.
"""

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class SeedStep:
    """One idempotent unit of seeding."""

    name: str
    run: Callable[[], None]
    clear: Callable[[], None] | None = None


_STEPS: list[SeedStep] = []


def register(step: SeedStep) -> None:
    """Append `step` to the registry. Steps run in the order they are registered."""
    _STEPS.append(step)


def registered() -> tuple[SeedStep, ...]:
    """The steps that will run, in order."""
    return tuple(_STEPS)


def clear_registry() -> None:
    """Drop every registered step. Exists so tests can isolate their own fixtures."""
    _STEPS.clear()
