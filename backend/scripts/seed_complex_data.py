import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulate_batch import seed_complex_data


if __name__ == "__main__":
    seed_complex_data()
    print("Complex data seeded")
