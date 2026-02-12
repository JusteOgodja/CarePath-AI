from __future__ import annotations

import argparse
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.mask import mask
from shapely.geometry import Point
from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.models import CentreModel, get_session, init_db


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Calculate catchment population around centres")
    parser.add_argument("--raster", required=True, type=str, help="Path to WorldPop GeoTIFF")
    parser.add_argument("--radius-km", type=float, default=10.0)
    return parser.parse_args()


def catchment_sum(dataset: rasterio.io.DatasetReader, lat: float, lon: float, radius_km: float) -> int:
    center = gpd.GeoSeries([Point(lon, lat)], crs="EPSG:4326")
    projected = center.to_crs("EPSG:3857")
    buffered = projected.buffer(radius_km * 1000.0)
    buffered_wgs84 = gpd.GeoSeries(buffered, crs="EPSG:3857").to_crs("EPSG:4326")

    geom = [buffered_wgs84.iloc[0].__geo_interface__]
    out, _ = mask(dataset, geom, crop=True, filled=True, nodata=np.nan)
    arr = out[0]
    valid = np.where(np.isnan(arr), 0.0, arr)
    total = float(valid.sum())
    return max(0, int(round(total)))


def main() -> None:
    args = parse_args()
    init_db()

    raster_path = Path(args.raster)
    if not raster_path.exists():
        raise FileNotFoundError(f"Raster not found: {raster_path}")

    updated = 0
    skipped = 0
    with rasterio.open(raster_path) as dataset:
        with get_session() as session:
            centres = session.scalars(select(CentreModel)).all()
            for centre in centres:
                if centre.lat is None or centre.lon is None:
                    skipped += 1
                    continue
                population = catchment_sum(dataset, centre.lat, centre.lon, args.radius_km)
                centre.catchment_population = population
                updated += 1

            session.commit()

    print({"updated": updated, "skipped": skipped, "radius_km": args.radius_km})


if __name__ == "__main__":
    main()
