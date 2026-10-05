from ninja.testing import TestClient

from core.api import api

client = TestClient(api)


def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
