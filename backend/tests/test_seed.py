from io import StringIO

import pytest
from django.core.management import call_command

from core import seeding

pytestmark = pytest.mark.django_db


def test_seed_with_no_discovered_steps_is_a_noop(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(seeding, "discover", tuple)
    out = StringIO()

    call_command("seed", stdout=out)

    assert "nothing to seed" in out.getvalue()


def test_seed_with_no_steps_ignores_reset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(seeding, "discover", tuple)
    out = StringIO()

    call_command("seed", "--reset", stdout=out)

    assert "nothing to seed" in out.getvalue()


def test_seed_runs_steps_in_discovery_order(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []
    monkeypatch.setattr(
        seeding,
        "discover",
        lambda: (
            seeding.SeedStep(name="first", run=lambda: events.append("run:first")),
            seeding.SeedStep(name="second", run=lambda: events.append("run:second")),
        ),
    )

    call_command("seed", stdout=StringIO())

    assert events == ["run:first", "run:second"]


def test_seed_reports_the_step_count(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        seeding, "discover", lambda: (seeding.SeedStep(name="only", run=lambda: None),)
    )
    out = StringIO()

    call_command("seed", stdout=out)

    assert "1 step(s)" in out.getvalue()


def test_seed_without_reset_never_clears(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []
    monkeypatch.setattr(
        seeding,
        "discover",
        lambda: (
            seeding.SeedStep(
                name="only",
                run=lambda: events.append("run:only"),
                clear=lambda: events.append("clear:only"),
            ),
        ),
    )

    call_command("seed", stdout=StringIO())

    assert events == ["run:only"]


def test_reset_clears_before_seeding_in_reverse_order(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []
    monkeypatch.setattr(
        seeding,
        "discover",
        lambda: (
            seeding.SeedStep(
                name="first",
                run=lambda: events.append("run:first"),
                clear=lambda: events.append("clear:first"),
            ),
            seeding.SeedStep(
                name="second",
                run=lambda: events.append("run:second"),
                clear=lambda: events.append("clear:second"),
            ),
        ),
    )

    call_command("seed", "--reset", stdout=StringIO())

    assert events == ["clear:second", "clear:first", "run:first", "run:second"]


def test_reset_skips_steps_without_a_clear_hook(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []
    monkeypatch.setattr(
        seeding,
        "discover",
        lambda: (seeding.SeedStep(name="only", run=lambda: events.append("run:only")),),
    )

    call_command("seed", "--reset", stdout=StringIO())

    assert events == ["run:only"]


def test_a_failing_step_aborts_the_run(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []

    def explode() -> None:
        raise RuntimeError("seeder exploded")

    monkeypatch.setattr(
        seeding,
        "discover",
        lambda: (
            seeding.SeedStep(name="first", run=explode),
            seeding.SeedStep(name="second", run=lambda: events.append("run:second")),
        ),
    )

    with pytest.raises(RuntimeError, match="seeder exploded"):
        call_command("seed", stdout=StringIO())

    assert events == []


def test_discover_finds_the_catalog_seeder() -> None:
    """Update this list when another app adds a `seeders` module."""
    assert [step.name for step in seeding.discover()] == ["catalog"]


def test_discover_skips_apps_without_a_seeders_module() -> None:
    """`core` has no `seeders` module, so it contributes nothing."""
    assert all(step.name != "core" for step in seeding.discover())
