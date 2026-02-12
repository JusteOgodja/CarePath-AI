from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
DEFAULT_DATA_ROOT = REPO_ROOT / "data" / "kenya"


def run_cmd(cmd: list[str]) -> None:
    print(f"[run] {' '.join(cmd)}")
    subprocess.run(cmd, cwd=BACKEND_DIR, check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="One-command Kenya data pipeline for CarePath")
    parser.add_argument("--reset-db", action="store_true", help="Delete existing backend/carepath.db before running")
    parser.add_argument("--data-root", type=str, default=str(DEFAULT_DATA_ROOT))
    parser.add_argument(
        "--pois-shp",
        type=str,
        default=None,
        help="Override Geofabrik POI shapefile path (default: <data-root>/Geofabrik/gis_osm_pois_free_1.shp)",
    )
    parser.add_argument(
        "--worldpop-raster",
        type=str,
        default=None,
        help="Override WorldPop raster path (default: <data-root>/WorldPop Kenya 100m resolution/ken_ppp_2020_UNadj.tif)",
    )
    parser.add_argument("--radius-km", type=float, default=10.0)
    parser.add_argument("--beds-per-10000", type=float, default=None, help="Manual override. If omitted, inferred from indicator profile")
    parser.add_argument("--availability-ratio", type=float, default=0.8)
    parser.add_argument("--k-nearest", type=int, default=3)
    parser.add_argument("--speed-kmh", type=float, default=40.0)
    parser.add_argument("--targets-per-centre", type=int, default=2)
    parser.add_argument("--patients", type=int, default=200)
    return parser.parse_args()


def load_beds_from_profile(path: Path) -> float:
    payload = json.loads(path.read_text(encoding="utf-8"))
    profile = payload.get("profile", {})
    beds = profile.get("beds_per_10000")
    if beds is None:
        raise ValueError(f"beds_per_10000 missing in {path}")
    return float(beds)


def pick_existing_source_id(db_path: Path) -> str:
    with sqlite3.connect(str(db_path)) as conn:
        row = conn.execute("SELECT id FROM centres ORDER BY id LIMIT 1").fetchone()
    if row is None or not row[0]:
        raise ValueError("No centres found in DB after import")
    return str(row[0])


def main() -> None:
    args = parse_args()

    db_path = BACKEND_DIR / "carepath.db"
    if args.reset_db and db_path.exists():
        print(f"[info] deleting DB: {db_path}")
        db_path.unlink()

    data_root = Path(args.data_root)
    pois_shp = Path(args.pois_shp) if args.pois_shp else data_root / "Geofabrik" / "gis_osm_pois_free_1.shp"
    worldpop_raster = (
        Path(args.worldpop_raster)
        if args.worldpop_raster
        else data_root / "WorldPop Kenya 100m resolution" / "ken_ppp_2020_UNadj.tif"
    )

    if not pois_shp.exists():
        raise FileNotFoundError(f"Missing shapefile: {pois_shp}")
    if not worldpop_raster.exists():
        raise FileNotFoundError(f"Missing WorldPop raster: {worldpop_raster}")

    run_cmd([sys.executable, "scripts/init_db.py"])
    run_cmd(
        [
            sys.executable,
            "scripts/import_geofabrik_pois.py",
            "--input-shp",
            str(pois_shp),
            "--include-fclass",
            "hospital,clinic,doctors,dentist",
            "--exclude-empty-name",
        ]
    )
    run_cmd(
        [
            sys.executable,
            "scripts/calc_catchment_population.py",
            "--raster",
            str(worldpop_raster),
            "--radius-km",
            str(args.radius_km),
        ]
    )
    run_cmd(
        [
            sys.executable,
            "scripts/import_wdi_indicators.py",
            "--input-dir",
            str(data_root),
            "--country-code",
            "KEN",
            "--latest-only",
        ]
    )
    profile_path = BACKEND_DIR / "docs" / "indicator_profile.json"
    run_cmd(
        [
            sys.executable,
            "scripts/build_indicator_profile.py",
            "--country-code",
            "KEN",
            "--output",
            str(profile_path.relative_to(BACKEND_DIR)),
        ]
    )

    beds_per_10000 = args.beds_per_10000 if args.beds_per_10000 is not None else load_beds_from_profile(profile_path)
    run_cmd(
        [
            sys.executable,
            "scripts/calibrate_capacity.py",
            "--beds-per-10000",
            f"{beds_per_10000:.6f}",
            "--availability-ratio",
            str(args.availability_ratio),
        ]
    )
    run_cmd(
        [
            sys.executable,
            "scripts/build_edges_from_geo.py",
            "--k-nearest",
            str(args.k_nearest),
            "--speed-kmh",
            str(args.speed_kmh),
            "--bidirectional",
        ]
    )
    run_cmd(
        [
            sys.executable,
            "scripts/repair_isolated_edges.py",
            "--include-partially-isolated",
            "--targets-per-centre",
            str(args.targets_per_centre),
            "--output",
            "docs/isolated_repair_report_partial.json",
        ]
    )
    run_cmd(
        [
            sys.executable,
            "scripts/find_isolated_centres.py",
            "--only-fully-isolated",
            "--output",
            "docs/isolated_centres_after_repair.json",
        ]
    )
    source_id = pick_existing_source_id(db_path)
    print(f"[info] final simulation source id: {source_id}")
    run_cmd(
        [
            sys.executable,
            "scripts/simulate_batch.py",
            "--patients",
            str(args.patients),
            "--source",
            source_id,
            "--policy",
            "heuristic",
            "--sample-source-by-catchment",
            "--case-mix-mode",
            "mixed",
            "--severity-mode",
            "mixed",
            "--maternal-ratio",
            "0.399",
            "--pediatric-ratio",
            "0.3995",
            "--general-ratio",
            "0.2015",
            "--severity-low-ratio",
            "0.3324",
            "--severity-medium-ratio",
            "0.4633",
            "--severity-high-ratio",
            "0.2043",
            "--fallback-policy",
            "none",
        ]
    )

    print("[done] Kenya pipeline completed.")
    print("[artifacts] backend/docs/indicator_profile.json")
    print("[artifacts] backend/docs/isolated_repair_report_partial.json")
    print("[artifacts] backend/docs/isolated_centres_after_repair.json")


if __name__ == "__main__":
    main()
