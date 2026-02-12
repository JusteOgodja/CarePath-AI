import sys
from pathlib import Path

import pytest

from app.db.models import CentreModel, get_session

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from import_geofabrik_pois import infer_level_from_fclass, load_pois_from_shapefile, to_centre, upsert_centres


def test_geofabrik_mapping_levels() -> None:
    assert infer_level_from_fclass("hospital", "County Hospital") == "secondary"
    assert infer_level_from_fclass("hospital", "County Referral Hospital") == "tertiary"
    assert infer_level_from_fclass("clinic", "City Clinic") == "secondary"
    assert infer_level_from_fclass("doctors", "ABC Doctors") == "primary"
    assert infer_level_from_fclass("hospital", "Mikuyuni Dispensary") == "primary"
    assert infer_level_from_fclass("clinic") == "secondary"
    assert infer_level_from_fclass("doctors") == "primary"


def test_import_geofabrik_pois_from_temp_shapefile(tmp_path: Path) -> None:
    shapefile = pytest.importorskip("shapefile")

    shp_base = tmp_path / "pois"
    writer = shapefile.Writer(str(shp_base))
    writer.field("osm_id", "N", decimal=0)
    writer.field("code", "N", decimal=0)
    writer.field("fclass", "C", size=30)
    writer.field("name", "C", size=80)

    writer.point(36.8219, -1.2921)
    writer.record(1001, 1, "hospital", "Nairobi Hospital")
    writer.point(36.9000, -1.3000)
    writer.record(1002, 2, "clinic", "City Clinic")
    writer.close()

    rows = load_pois_from_shapefile(shp_base.with_suffix(".shp"))
    centres = [to_centre(r) for r in rows]
    inserted, updated = upsert_centres(centres)

    assert inserted == 2
    assert updated == 0

    with get_session() as session:
        all_centres = session.query(CentreModel).all()

    assert len(all_centres) == 2
    levels = {c.level for c in all_centres}
    assert levels == {"secondary"}
