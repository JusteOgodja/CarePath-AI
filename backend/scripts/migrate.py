import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.migrations import run_migrations


if __name__ == "__main__":
    ok = run_migrations()
    if ok:
        print("Alembic migration applied (head).")
    else:
        raise SystemExit("Alembic is not installed. Install backend requirements/dev dependencies first.")
