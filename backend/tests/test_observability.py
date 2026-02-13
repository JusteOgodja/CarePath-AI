from fastapi.testclient import TestClient

from app.main import app

API_PREFIX = "/api/v1"


def test_health_contains_runtime_fields() -> None:
    client = TestClient(app)
    response = client.get(f"{API_PREFIX}/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "degraded"}
    assert body["database"] in {"ok", "error"}
    assert "time_utc" in body


def test_request_id_header_is_set() -> None:
    client = TestClient(app)
    response = client.get(f"{API_PREFIX}/health")
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID")


def test_http_error_payload_is_standardized() -> None:
    client = TestClient(app)
    response = client.get(f"{API_PREFIX}/missing-endpoint")
    assert response.status_code == 404
    body = response.json()
    assert "detail" in body
    assert "error" in body
    assert body["error"]["code"] == "http_404"
    assert body["error"]["request_id"] is not None
