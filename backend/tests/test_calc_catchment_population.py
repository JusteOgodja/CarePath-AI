import sys
from pathlib import Path

import numpy as np
import pytest

from app.db.models import CentreModel, get_session

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def test_population_calculation_with_mock_raster(tmp_path: Path) -> None:
    rasterio = pytest.importorskip("rasterio")
    pytest.importorskip("geopandas")
    from rasterio.transform import from_origin
    from calc_catchment_population import catchment_sum

    raster_path = tmp_path / "pop.tif"
    arr = np.full((10, 10), 10, dtype=np.float32)
    transform = from_origin(2.95, 6.25, 0.01, 0.01)

    with rasterio.open(
        raster_path,
        "w",
        driver="GTiff",
        height=arr.shape[0],
        width=arr.shape[1],
        count=1,
        dtype=arr.dtype,
        crs="EPSG:4326",
        transform=transform,
    ) as dst:
        dst.write(arr, 1)

    with get_session() as session:
        centre = CentreModel(
            id="POP_TEST",
            name="Pop Test",
            lat=6.20,
            lon=3.00,
            osm_type="node",
            osm_id="pop_test",
            level="primary",
            specialities="general",
            raw_tags_json="{}",
            capacity_max=10,
            capacity_available=10,
            estimated_wait_minutes=15,
            catchment_population=0,
        )
        session.add(centre)
        session.commit()

    with rasterio.open(raster_path) as ds:
        population = catchment_sum(ds, 6.20, 3.00, radius_km=5.0)

    assert population > 0
