from fastapi.testclient import TestClient

from app.main import app

API_PREFIX = "/api/v1"


def test_login_returns_token_for_admin() -> None:
    client = TestClient(app)
    response = client.post(
        f"{API_PREFIX}/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["role"] == "admin"
    assert body["access_token"]


def test_admin_write_requires_token() -> None:
    client = TestClient(app)
    payload = {
        "id": "AUTH_C1",
        "name": "Auth Centre",
        "level": "secondary",
        "specialities": ["general"],
        "capacity_available": 2,
        "estimated_wait_minutes": 15,
    }
    response = client.post(f"{API_PREFIX}/centres", json=payload)
    assert response.status_code == 401


def test_viewer_cannot_write_admin_resources() -> None:
    client = TestClient(app)
    login = client.post(
        f"{API_PREFIX}/auth/login",
        json={"username": "viewer", "password": "viewer123"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    payload = {
        "id": "AUTH_C2",
        "name": "Viewer Centre",
        "level": "secondary",
        "specialities": ["general"],
        "capacity_available": 2,
        "estimated_wait_minutes": 15,
    }
    response = client.post(
        f"{API_PREFIX}/centres",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_login_rate_limit_kicks_in() -> None:
    client = TestClient(app)
    status_codes: list[int] = []
    for _ in range(11):
        response = client.post(
            f"{API_PREFIX}/auth/login",
            json={"username": "admin", "password": "wrong-password"},
        )
        status_codes.append(response.status_code)

    assert 429 in status_codes
