import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.models import CentreModel, ReferenceModel, get_session, init_db


def seed_demo_data() -> None:
    init_db()
    with get_session() as session:
        session.query(ReferenceModel).delete()
        session.query(CentreModel).delete()

        centres = [
            CentreModel(
                id="C_LOCAL_A",
                name="Centre Local A",
                level="primary",
                specialities="general,maternal",
                capacity_available=3,
                estimated_wait_minutes=30,
            ),
            CentreModel(
                id="C_LOCAL_B",
                name="Centre Local B",
                level="primary",
                specialities="general",
                capacity_available=2,
                estimated_wait_minutes=20,
            ),
            CentreModel(
                id="H_DISTRICT_1",
                name="Hopital District 1",
                level="secondary",
                specialities="general,maternal,pediatric",
                capacity_available=4,
                estimated_wait_minutes=45,
            ),
            CentreModel(
                id="H_REGIONAL_1",
                name="Hopital Regional 1",
                level="tertiary",
                specialities="maternal,pediatric",
                capacity_available=6,
                estimated_wait_minutes=35,
            ),
        ]

        refs = [
            ReferenceModel(source_id="C_LOCAL_A", dest_id="H_DISTRICT_1", travel_minutes=20),
            ReferenceModel(source_id="C_LOCAL_B", dest_id="H_DISTRICT_1", travel_minutes=15),
            ReferenceModel(source_id="H_DISTRICT_1", dest_id="H_REGIONAL_1", travel_minutes=35),
            ReferenceModel(source_id="C_LOCAL_A", dest_id="H_REGIONAL_1", travel_minutes=60),
            ReferenceModel(source_id="C_LOCAL_B", dest_id="H_REGIONAL_1", travel_minutes=70),
        ]

        session.add_all(centres)
        session.add_all(refs)
        session.commit()


if __name__ == "__main__":
    seed_demo_data()
    print("Demo data seeded in carepath.db")
