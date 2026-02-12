import os


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", "sqlite:///./carepath.db")

