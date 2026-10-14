"""The API mounting, and the error envelope's last resort (`API.md` section 3, `NFR-4`).

`core/errors.py` replaces Ninja's default handlers so that a bug answers in the documented shape
rather than reaching Django and producing a non-JSON body. That handler is the one branch no
endpoint can reach on purpose, so it is exercised on a throwaway `NinjaAPI` carrying a route that
raises — the app's own router has nothing in it that fails on demand.
"""

from typing import Any

import pytest
from django.test import Client
from ninja import NinjaAPI
from ninja.testing import TestClient

from core.errors import install_error_handlers

pytestmark = pytest.mark.django_db


def test_openapi_schema_is_served() -> None:
    response = Client().get("/api/v1/openapi.json")
    assert response.status_code == 200
    assert response.json()["info"]["title"] == "LYSHEIM API"


def test_an_unhandled_error_answers_in_the_envelope_and_reaches_the_log(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """`NFR-5`: an unexpected failure is logged *and* answered in the one error shape.

    Both halves are asserted, because either one alone is a bug: without the log the envelope would
    hide the cause entirely, and without the envelope the client would be handed a stack trace
    instead of a code it can switch on. The exception's own message is the part most likely to name
    a table or a host, so it stays in the log and out of the body.
    """
    api = NinjaAPI()

    @api.get("/boom")
    def boom(request: Any) -> None:
        raise RuntimeError("the database went for a walk")

    install_error_handlers(api)

    with caplog.at_level("ERROR"):
        response = TestClient(api).get("/boom")

    assert response.status_code == 500
    error = response.json()["error"]
    assert set(error) == {"code", "message", "details", "request_id"}
    assert error["code"] == "INTERNAL_ERROR"
    assert error["message"] == "An unexpected error occurred."
    assert error["details"] == []
    assert "the database went for a walk" not in response.content.decode()
    assert "the database went for a walk" in caplog.text
