"""`manage.py export_openapi_schema` — write the OpenAPI contract to `frontend/openapi.json`.

The frontend generates its TypeScript types from this file (`M1.4`), so it is a committed
artifact rather than something fetched at build time: `Frontend CI` has no backend to fetch from,
and a Vercel build must not depend on one. `Backend CI` regenerates it and fails on any
difference, which is what keeps the contract from drifting silently (`API.md` section 10).

django-ninja ships an `export_openapi_schema` command of its own, but Django only discovers
management commands from applications in `INSTALLED_APPS`, and `ninja` is not one of them. Its
default also resolves the API instance at `/api/`, where this project mounts `/api/v1`. This
wrapper pins both the instance and the output path, so the drift check and a developer run the
same command with no arguments.
"""

import json
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.utils.module_loading import import_string
from ninja import NinjaAPI
from ninja.responses import NinjaJSONEncoder

API_PATH = "config.api.api"


class Command(BaseCommand):
    help = "Write the OpenAPI schema to frontend/openapi.json (the frontend's type source)."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--api",
            default=API_PATH,
            help=f"Import path of the NinjaAPI instance (default: {API_PATH}).",
        )
        parser.add_argument(
            "--output",
            default=None,
            help="Output path (default: <repo>/frontend/openapi.json).",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        api = _import_api(options["api"])

        # Sorted keys and a fixed indent keep the file diff-friendly, so a contract change shows
        # up as the lines that actually changed. That reviewability is the point of committing it.
        schema = api.get_openapi_schema()
        result = json.dumps(schema, cls=NinjaJSONEncoder, indent=2, sort_keys=True)
        result += "\n"

        output = Path(options["output"]) if options["output"] else _default_output()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(result, encoding="utf-8")

        self.stdout.write(self.style.SUCCESS(f"Wrote {output}"))


def _import_api(path: str) -> NinjaAPI:
    api = import_string(path)
    if not isinstance(api, NinjaAPI):
        raise CommandError(f"{path} is not a NinjaAPI instance.")
    return api


def _default_output() -> Path:
    """The frontend is `BASE_DIR`'s sibling, and the file has to live inside it for Vercel."""
    return Path(settings.BASE_DIR).parent / "frontend" / "openapi.json"
