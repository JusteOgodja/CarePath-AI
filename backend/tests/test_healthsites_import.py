import json
import sys
from pathlib import Path

from app.db.models import CentreModel, get_session
from app.integrations.healthsites_client import HealthsitesClient

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from import_healthsites import facility_to_centre, upsert_centres


def test_healthsites_import_parses_and_upserts(monkeypatch) -> None:
    calls = []

    def fake_fetch_page(self, query):
        calls.append(query.page)
        if query.page == 1:
            return {
                "results": [
                    {
                        "properties": {
                            "name": "Alpha Clinic",
                            "osm_type": "node",
                            "osm_id": "1001",
                            "amenity": "clinic",
                            "healthcare:speciality": "pediatric",
                        },
                        "geometry": {"coordinates": [3.0, 6.0]},
                    }
                ],
                "next": "page2",
            }
        return {"results": [], "next": None}

    monkeypatch.setattr(HealthsitesClient, "fetch_page", fake_fetch_page)
    client = HealthsitesClient(base_url="https://healthsites.io")

    items = list(
        client.iter_facilities(
            api_key="dummy",
            country="CM",
            extent=None,
            date_from=None,
            date_to=None,
            flat_properties=True,
            tag_format="osm",
            output="json",
            max_pages=5,
        )
    )
    assert calls == [1, 2]
    assert len(items) == 1

    mapped = [facility_to_centre(items[0])]
    inserted, updated = upsert_centres(mapped)
    assert inserted == 1
    assert updated == 0

    # Re-import with same osm identity to verify upsert updates existing row.
    item2 = {
        "properties": {
            "name": "Alpha Clinic Updated",
            "osm_type": "node",
            "osm_id": "1001",
            "amenity": "clinic",
            "healthcare:speciality": "pediatric",
        },
        "geometry": {"coordinates": [3.2, 6.1]},
    }
    mapped2 = [facility_to_centre(item2)]
    inserted2, updated2 = upsert_centres(mapped2)
    assert inserted2 == 0
    assert updated2 == 1

    with get_session() as session:
        centre = session.query(CentreModel).filter(CentreModel.osm_id == "1001").one()
        assert centre.name == "Alpha Clinic Updated"
        assert centre.level == "secondary"
        assert "pediatric" in centre.specialities
        assert json.loads(centre.raw_tags_json)["amenity"] == "clinic"
