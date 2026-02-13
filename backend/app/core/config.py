import os
from pathlib import Path


def get_database_url() -> str:
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return db_url
    default_db = Path(__file__).resolve().parents[2] / "carepath.db"
    return f"sqlite:///{default_db.as_posix()}"


def get_healthsites_api_key() -> str:
    key = os.getenv("HEALTHSITES_API_KEY", "").strip()
    if not key:
        raise ValueError("HEALTHSITES_API_KEY is required")
    return key


def get_healthsites_base_url() -> str:
    return os.getenv("HEALTHSITES_BASE_URL", "https://healthsites.io").rstrip("/")


def get_cors_allow_origins() -> list[str]:
    value = os.getenv("CORS_ALLOW_ORIGINS", "").strip()
    if value:
        origins = [item.strip().rstrip("/") for item in value.split(",") if item.strip()]
        if origins:
            return origins

    return [
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ]
