from django.test import Client


def test_healthz_returns_ok() -> None:
    response = Client().get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_healthz_sets_request_id_header() -> None:
    response = Client().get("/healthz")
    assert response["X-Request-ID"]


def test_healthz_echoes_supplied_request_id() -> None:
    response = Client().get("/healthz", headers={"X-Request-ID": "abc123"})
    assert response["X-Request-ID"] == "abc123"
    assert response.json()["request_id"] == "abc123"
