import os
from pathlib import Path


def get_database_url() -> str:
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return db_url
    default_db = Path(__file__).resolve().parents[2] / "carepath.db"
    return f"sqlite:///{default_db.as_posix()}"


def get_app_env() -> str:
    return os.getenv("APP_ENV", "development").strip().lower()


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


def get_auth_secret_key() -> str:
    return os.getenv("AUTH_SECRET_KEY", "change-this-in-production")


def get_token_expire_seconds() -> int:
    raw = os.getenv("AUTH_TOKEN_EXPIRE_SECONDS", "28800").strip()
    try:
        value = int(raw)
    except ValueError:
        value = 28800
    return max(300, value)


def get_admin_credentials() -> tuple[str, str]:
    username = os.getenv("ADMIN_USERNAME", "admin").strip()
    password = os.getenv("ADMIN_PASSWORD", "admin123").strip()
    return username, password


def get_viewer_credentials() -> tuple[str, str]:
    username = os.getenv("VIEWER_USERNAME", "viewer").strip()
    password = os.getenv("VIEWER_PASSWORD", "viewer123").strip()
    return username, password


def get_recommendation_policy_default() -> str:
    return os.getenv("RECOMMENDATION_POLICY_DEFAULT", "auto").strip().lower()


def get_rl_model_path() -> str:
    value = os.getenv("RL_MODEL_PATH", "").strip()
    if value:
        return value
    default_model = Path(__file__).resolve().parents[2] / "models" / "ppo_referral.zip"
    return str(default_model)


def validate_runtime_config() -> None:
    env = get_app_env()
    if env not in {"production", "prod"}:
        return

    if get_auth_secret_key() == "change-this-in-production":
        raise ValueError("AUTH_SECRET_KEY must be set to a strong secret in production")

    admin_user, admin_pass = get_admin_credentials()
    viewer_user, viewer_pass = get_viewer_credentials()
    weak_defaults = {
        ("admin", "admin123"),
        ("viewer", "viewer123"),
    }
    if (admin_user, admin_pass) in weak_defaults or (viewer_user, viewer_pass) in weak_defaults:
        raise ValueError("Default credentials are not allowed in production")
