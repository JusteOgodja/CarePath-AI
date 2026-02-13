from __future__ import annotations

from pathlib import Path


def run_migrations() -> bool:
    try:
        from alembic import command
        from alembic.config import Config
    except Exception:
        return False

    root = Path(__file__).resolve().parents[2]
    cfg = Config(str(root / "alembic.ini"))
    command.upgrade(cfg, "head")
    return True
