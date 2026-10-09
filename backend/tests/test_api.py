from django.test import Client


def test_openapi_schema_is_served() -> None:
    response = Client().get("/api/v1/openapi.json")
    assert response.status_code == 200
    assert response.json()["info"]["title"] == "LYSHEIM API"
