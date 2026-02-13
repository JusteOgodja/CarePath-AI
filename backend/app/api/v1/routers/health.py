from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import text

from app.db.models import engine

router = APIRouter(tags=["health"])


@router.get("/health")
def healthcheck() -> dict[str, str | None]:
    db_status = "ok"
    schema_revision: str | None = None
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            try:
                schema_revision = conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).scalar()
            except Exception:
                schema_revision = None
    except Exception:
        db_status = "error"

    status = "ok" if db_status == "ok" else "degraded"
    return {
        "status": status,
        "database": db_status,
        "schema_revision": schema_revision,
        "time_utc": datetime.now(timezone.utc).isoformat(),
    }
