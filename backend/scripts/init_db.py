import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.migrations import run_migrations
from app.db.models import init_db


if __name__ == "__main__":
    if run_migrations():
        print("Database migrated to head")
    else:
        init_db()
        print("Database initialized (fallback without Alembic)")
