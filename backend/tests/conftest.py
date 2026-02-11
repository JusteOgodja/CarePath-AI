import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.models import CentreModel, ReferenceModel, get_session, init_db


@pytest.fixture(scope="session", autouse=True)
def init_database() -> None:
    init_db()


@pytest.fixture(autouse=True)
def clean_db() -> None:
    with get_session() as session:
        session.query(ReferenceModel).delete()
        session.query(CentreModel).delete()
        session.commit()
    yield
    with get_session() as session:
        session.query(ReferenceModel).delete()
        session.query(CentreModel).delete()
        session.commit()


@pytest.fixture
def client() -> TestClient:
    from app.main import app

    return TestClient(app)
