import sys
from pathlib import Path

from app.db.models import CentreModel, ReferenceModel, get_session

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from build_edges_from_geo import build_edges


def test_build_edges_creates_references_with_travel_minutes() -> None:
    with get_session() as session:
        session.add_all(
            [
                CentreModel(
                    id="P1",
                    name="Primary 1",
                    lat=6.0,
                    lon=3.0,
                    osm_type="node",
                    osm_id="p1",
                    level="primary",
                    specialities="general,maternal",
                    raw_tags_json="{}",
                    capacity_max=10,
                    capacity_available=10,
                    estimated_wait_minutes=15,
                ),
                CentreModel(
                    id="S1",
                    name="Secondary 1",
                    lat=6.1,
                    lon=3.1,
                    osm_type="node",
                    osm_id="s1",
                    level="secondary",
                    specialities="general,maternal",
                    raw_tags_json="{}",
                    capacity_max=30,
                    capacity_available=30,
                    estimated_wait_minutes=30,
                ),
                CentreModel(
                    id="T1",
                    name="Tertiary 1",
                    lat=6.2,
                    lon=3.2,
                    osm_type="node",
                    osm_id="t1",
                    level="tertiary",
                    specialities="general,maternal,pediatric",
                    raw_tags_json="{}",
                    capacity_max=120,
                    capacity_available=120,
                    estimated_wait_minutes=60,
                ),
            ]
        )
        session.commit()

    created, skipped = build_edges(
        k_nearest=1,
        speed_kmh=40.0,
        replace=True,
        with_alternatives=False,
        bidirectional=False,
        osrm_server=None,
    )
    assert created == 2
    assert skipped == 0

    with get_session() as session:
        refs = session.query(ReferenceModel).all()

    assert len(refs) == 2
    pair_set = {(r.source_id, r.dest_id) for r in refs}
    assert ("P1", "S1") in pair_set
    assert ("S1", "T1") in pair_set
    assert all(r.travel_minutes > 0 for r in refs)
