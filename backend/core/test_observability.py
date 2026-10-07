"""NFR-5 (`ARCHITECTURE.md` §11): request ids, structured logs, one error shape."""

from __future__ import annotations

import json
import logging
import uuid

import pytest

from core.logging import JsonFormatter, RequestIDFilter, set_request_id

HEALTH = "/api/v1/health"


def _record(message: str = "hello %s", args: tuple[object, ...] = ("world",)) -> logging.LogRecord:
    return logging.LogRecord(
        name="nordvik.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg=message,
        args=args,
        exc_info=None,
    )


def test_every_response_carries_a_request_id(client):
    response = client.get(HEALTH)

    assert response.status_code == 200
    uuid.UUID(response["X-Request-ID"])


def test_a_caller_supplied_request_id_is_echoed(client):
    supplied = str(uuid.uuid4())

    response = client.get(HEALTH, headers={"X-Request-ID": supplied})

    assert response["X-Request-ID"] == supplied


@pytest.mark.parametrize("bogus", ["not-a-uuid", "", "1", "'; DROP TABLE users;--", "../../etc"])
def test_a_bogus_request_id_is_replaced_rather_than_trusted(client, bogus):
    """A caller must not be able to inject arbitrary text into the logs."""
    response = client.get(HEALTH, headers={"X-Request-ID": bogus})

    assert response["X-Request-ID"] != bogus
    uuid.UUID(response["X-Request-ID"])


def test_log_lines_are_single_json_objects():
    formatted = JsonFormatter().format(_record())

    assert "\n" not in formatted
    payload = json.loads(formatted)
    assert payload["message"] == "hello world"
    assert payload["level"] == "INFO"
    assert payload["logger"] == "nordvik.test"
    assert "time" in payload


def test_log_lines_carry_the_request_id():
    set_request_id("11111111-2222-3333-4444-555555555555")
    try:
        record = _record()
        RequestIDFilter().filter(record)
        payload = json.loads(JsonFormatter().format(record))
    finally:
        set_request_id(None)

    assert payload["request_id"] == "11111111-2222-3333-4444-555555555555"


def test_http_errors_use_the_documented_envelope(client):
    response = client.get("/api/v1/orders")

    body = response.json()
    assert response.status_code == 401
    assert body["code"] == "unauthorized"
    assert body["errors"] == {}
    assert isinstance(body["detail"], str)
    assert body["request_id"] == response["X-Request-ID"]


def test_validation_errors_use_the_documented_envelope(client):
    response = client.post(
        "/api/v1/auth/register",
        data=json.dumps({"email": "not-an-email"}),
        content_type="application/json",
    )

    body = response.json()
    assert response.status_code == 422
    assert body["code"] == "validation_error"
    # A string, not a list: the frontend renders `detail` directly.
    assert isinstance(body["detail"], str)
    assert "password" in body["errors"]
    assert "email" in body["errors"]


def test_a_throttled_response_uses_the_documented_envelope(client, shopper):
    payload = json.dumps({"email": shopper.email, "password": "wrong"})
    for _ in range(10):
        client.post("/api/v1/auth/login", data=payload, content_type="application/json")

    response = client.post("/api/v1/auth/login", data=payload, content_type="application/json")

    assert response.status_code == 429
    assert response.json()["code"] == "rate_limited"
