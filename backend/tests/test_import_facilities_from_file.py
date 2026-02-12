import json
import sys
from pathlib import Path

from app.db.models import CentreModel, get_session

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from import_facilities_from_file import parse_geojson, to_centre, upsert_centres


def test_import_from_file_geojson_inserts_expected_centres(tmp_path: Path) -> None:
    sample = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [3.0, 6.0]},
                "properties": {
                    "name": "Clinic A",
                    "facility_type": "clinic",
                    "osm_type": "node",
                    "osm_id": "9001",
                    "healthcare:speciality": "pediatric",
                },
            },
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [3.1, 6.1]},
                "properties": {
                    "name": "Hospital B",
                    "facility_type": "hospital",
                    "osm_type": "way",
                    "osm_id": "9002",
                    "healthcare:speciality": "maternity",
                },
            },
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [3.2, 6.2]},
                "properties": {
                    "name": "County Referral Hospital C",
                    "facility_type": "hospital",
                    "osm_type": "way",
                    "osm_id": "9003",
                    "healthcare:speciality": "maternity",
                },
            },
        ],
    }
    path = tmp_path / "facilities.geojson"
    path.write_text(json.dumps(sample), encoding="utf-8")

    # Build minimal args-like object manually.
    class A:
        name_column = "name"
        facility_type_column = "facility_type"
        lat_column = "lat"
        lon_column = "lon"
        osm_type_column = "osm_type"
        osm_id_column = "osm_id"

    rows = parse_geojson(path)
    centres = [to_centre(r, A) for r in rows]
    inserted, updated = upsert_centres(centres)

    assert inserted == 3
    assert updated == 0

    with get_session() as session:
        all_centres = session.query(CentreModel).all()

    assert len(all_centres) == 3
    levels = {c.level for c in all_centres}
    assert "secondary" in levels
    assert "tertiary" in levels
    assert all(c.catchment_population == 0 for c in all_centres)
