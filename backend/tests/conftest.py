import sys
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_carepath.db")

from app.db.migrations import run_migrations
from app.db.models import CountryIndicatorModel, CentreModel, ReferenceModel, ReferralRequestModel, get_session, init_db
from app.core.rate_limit import reset_rate_limits


API_PREFIX = "/api/v1"


class PrefixedClient:
    def __init__(self, client: TestClient, prefix: str, token: str | None = None) -> None:
        self._client = client
        self._prefix = prefix.rstrip("/")
        self._token = token

    def _with_prefix(self, path: str) -> str:
        if not path.startswith("/"):
            return path
        return f"{self._prefix}{path}"

    def _with_auth_headers(self, kwargs: dict) -> dict:
        if not self._token:
            return kwargs
        headers = dict(kwargs.get("headers") or {})
        headers.setdefault("Authorization", f"Bearer {self._token}")
        kwargs["headers"] = headers
        return kwargs

    def request(self, method: str, path: str, *args, **kwargs):
        if method.upper() in {"POST", "PUT", "PATCH", "DELETE"}:
            kwargs = self._with_auth_headers(kwargs)
        return self._client.request(method, self._with_prefix(path), *args, **kwargs)

    def get(self, path: str, *args, **kwargs):
        return self._client.get(self._with_prefix(path), *args, **kwargs)

    def post(self, path: str, *args, **kwargs):
        kwargs = self._with_auth_headers(kwargs)
        return self._client.post(self._with_prefix(path), *args, **kwargs)

    def put(self, path: str, *args, **kwargs):
        kwargs = self._with_auth_headers(kwargs)
        return self._client.put(self._with_prefix(path), *args, **kwargs)

    def delete(self, path: str, *args, **kwargs):
        kwargs = self._with_auth_headers(kwargs)
        return self._client.delete(self._with_prefix(path), *args, **kwargs)

    def __getattr__(self, name: str):
        return getattr(self._client, name)


@pytest.fixture(scope="session", autouse=True)
def init_database() -> None:
    if not run_migrations():
        init_db()


@pytest.fixture(autouse=True)
def clean_db() -> None:
    reset_rate_limits()
    with get_session() as session:
        session.query(CountryIndicatorModel).delete()
        session.query(ReferralRequestModel).delete()
        session.query(ReferenceModel).delete()
        session.query(CentreModel).delete()
        session.commit()
    yield
    with get_session() as session:
        session.query(CountryIndicatorModel).delete()
        session.query(ReferralRequestModel).delete()
        session.query(ReferenceModel).delete()
        session.query(CentreModel).delete()
        session.commit()


@pytest.fixture
def client() -> PrefixedClient:
    from app.main import app

    raw_client = TestClient(app)
    auth = raw_client.post(
        f"{API_PREFIX}/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    token = auth.json().get("access_token") if auth.status_code == 200 else None
    return PrefixedClient(raw_client, API_PREFIX, token=token)
