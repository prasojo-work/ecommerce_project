from collections.abc import Iterator
from io import StringIO

import pytest
from django.core.management import call_command

from core import seeding

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _isolated_registry() -> Iterator[None]:
    """Keep each test's steps out of the module-level registry."""
    seeding.clear_registry()
    yield
    seeding.clear_registry()


def test_seed_with_no_registered_steps_is_a_noop() -> None:
    out = StringIO()

    call_command("seed", stdout=out)

    assert "nothing to seed" in out.getvalue()


def test_seed_with_no_registered_steps_ignores_reset() -> None:
    out = StringIO()

    call_command("seed", "--reset", stdout=out)

    assert "nothing to seed" in out.getvalue()


def test_seed_runs_steps_in_registration_order() -> None:
    events: list[str] = []
    seeding.register(seeding.SeedStep(name="first", run=lambda: events.append("run:first")))
    seeding.register(seeding.SeedStep(name="second", run=lambda: events.append("run:second")))

    call_command("seed", stdout=StringIO())

    assert events == ["run:first", "run:second"]


def test_seed_reports_the_step_count() -> None:
    seeding.register(seeding.SeedStep(name="only", run=lambda: None))
    out = StringIO()

    call_command("seed", stdout=out)

    assert "1 step(s)" in out.getvalue()


def test_seed_without_reset_never_clears() -> None:
    events: list[str] = []
    seeding.register(
        seeding.SeedStep(
            name="only",
            run=lambda: events.append("run:only"),
            clear=lambda: events.append("clear:only"),
        )
    )

    call_command("seed", stdout=StringIO())

    assert events == ["run:only"]


def test_reset_clears_before_seeding_in_reverse_order() -> None:
    events: list[str] = []
    seeding.register(
        seeding.SeedStep(
            name="first",
            run=lambda: events.append("run:first"),
            clear=lambda: events.append("clear:first"),
        )
    )
    seeding.register(
        seeding.SeedStep(
            name="second",
            run=lambda: events.append("run:second"),
            clear=lambda: events.append("clear:second"),
        )
    )

    call_command("seed", "--reset", stdout=StringIO())

    assert events == ["clear:second", "clear:first", "run:first", "run:second"]


def test_reset_skips_steps_without_a_clear_hook() -> None:
    events: list[str] = []
    seeding.register(seeding.SeedStep(name="only", run=lambda: events.append("run:only")))

    call_command("seed", "--reset", stdout=StringIO())

    assert events == ["run:only"]


def test_a_failing_step_aborts_the_run() -> None:
    events: list[str] = []

    def explode() -> None:
        raise RuntimeError("seeder exploded")

    seeding.register(seeding.SeedStep(name="first", run=explode))
    seeding.register(seeding.SeedStep(name="second", run=lambda: events.append("run:second")))

    with pytest.raises(RuntimeError, match="seeder exploded"):
        call_command("seed", stdout=StringIO())

    assert events == []


def test_registered_returns_a_snapshot_in_registration_order() -> None:
    seeding.register(seeding.SeedStep(name="first", run=lambda: None))
    seeding.register(seeding.SeedStep(name="second", run=lambda: None))

    assert [step.name for step in seeding.registered()] == ["first", "second"]
