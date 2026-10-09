"""`manage.py seed` — populate the database with demo data.

Idempotent by contract, with `--reset` to clear the seeded rows first. The seeders themselves
arrive with the catalog at `M1.2`; they plug into `core.seeding`. See
`docs/03-architecture/DATA-MODEL.md` for the seeding strategy.
"""

from typing import Any

from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction

from core import seeding


class Command(BaseCommand):
    help = "Seed the database with demo data (idempotent; --reset clears seeded rows first)."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete seeded rows before seeding, so the demo starts from a known state.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        steps = seeding.registered()
        if not steps:
            self.stdout.write("No seeders registered yet: nothing to seed or reset.")
            return

        # One transaction for the whole run, so a failure part-way through leaves no half-seeded
        # database and, under --reset, no wiped-but-unfilled one either.
        with transaction.atomic():
            if options["reset"]:
                self._clear(steps)
            for step in steps:
                self.stdout.write(f"Seeding {step.name}...")
                step.run()

        self.stdout.write(self.style.SUCCESS(f"Seed complete: {len(steps)} step(s)."))

    def _clear(self, steps: tuple[seeding.SeedStep, ...]) -> None:
        """Run every `clear` hook in reverse registration order."""
        for step in reversed(steps):
            if step.clear is None:
                continue
            self.stdout.write(f"Clearing {step.name}...")
            step.clear()
