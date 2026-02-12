from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.models import CentreModel, get_session, init_db

LEVEL_CAPACITY = {
    "primary": 10,
    "secondary": 30,
    "tertiary": 120,
}

LEVEL_WAIT = {
    "primary": 15,
    "secondary": 30,
    "tertiary": 60,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import facilities from local HDX/Healthsites files")
    parser.add_argument("--input", required=True, type=str, help="Path to GeoJSON or CSV file")
    parser.add_argument("--format", choices=["geojson", "csv"], default="geojson")
    parser.add_argument("--lat-column", type=str, default="lat")
    parser.add_argument("--lon-column", type=str, default="lon")
    parser.add_argument("--name-column", type=str, default="name")
    parser.add_argument("--facility-type-column", type=str, default="facility_type")
    parser.add_argument("--osm-type-column", type=str, default="osm_type")
    parser.add_argument("--osm-id-column", type=str, default="osm_id")
    return parser.parse_args()


def infer_level(facility_type: str, tags: dict[str, Any]) -> str:
    return infer_level_with_reason(facility_type, tags)[0]


def infer_level_with_reason(facility_type: str, tags: dict[str, Any]) -> tuple[str, str]:
    corpus = f"{facility_type} {' '.join(str(v) for v in tags.values())}".lower()
    if any(tok in corpus for tok in ["dispensary", "health_post", "health post", "outpost", "chemist"]):
        return "primary", "name_keyword_primary"
    if any(tok in corpus for tok in ["referral hospital", "county referral", "teaching hospital", "national hospital", "level 6", "level 5"]):
        return "tertiary", "name_keyword_tertiary"
    if any(tok in corpus for tok in ["doctors", "dentist", "pharmacy"]):
        return "primary", "fclass_primary"
    if any(tok in corpus for tok in ["health_center", "health centre", "health center", "clinic", "medical centre", "medical center"]):
        return "secondary", "name_keyword_secondary"
    if "hospital" in corpus:
        return "secondary", "hospital_default_secondary"
    return "primary", "fallback_primary"


def infer_specialities(facility_type: str, tags: dict[str, Any]) -> list[str]:
    corpus = f"{facility_type} {' '.join(str(v) for v in tags.values())}".lower()
    specialities: list[str] = []
    if any(tok in corpus for tok in ["maternal", "maternity", "obstetric", "antenatal", "prenatal"]):
        specialities.append("maternal")
    if any(tok in corpus for tok in ["pediatric", "paediatric", "children", "child"]):
        specialities.append("pediatric")
    if not specialities:
        specialities.append("general")
    elif "general" not in specialities:
        specialities.append("general")
    return specialities


def generate_id(name: str, osm_type: str | None, osm_id: str | None, lat: float | None, lon: float | None) -> str:
    if osm_type and osm_id:
        return f"FILE_{osm_type}_{osm_id}"
    digest = hashlib.sha1(f"{name}|{lat}|{lon}".encode("utf-8")).hexdigest()[:16]
    return f"FILE_FALLBACK_{digest}"


def parse_geojson(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    features = payload.get("features", [])
    rows: list[dict[str, Any]] = []
    for feature in features:
        props = dict(feature.get("properties") or {})
        geometry = feature.get("geometry") or {}
        coords = geometry.get("coordinates") if isinstance(geometry, dict) else None
        lon = coords[0] if isinstance(coords, list) and len(coords) >= 2 else props.get("lon")
        lat = coords[1] if isinstance(coords, list) and len(coords) >= 2 else props.get("lat")
        row = dict(props)
        row["lat"] = lat
        row["lon"] = lon
        rows.append(row)
    return rows


def parse_csv(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [dict(r) for r in reader]


def to_centre(row: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    name = str(row.get(args.name_column) or "Unnamed facility").strip()
    facility_type = str(row.get(args.facility_type_column) or "")

    lat_raw = row.get(args.lat_column)
    lon_raw = row.get(args.lon_column)
    lat = float(lat_raw) if lat_raw not in (None, "") else None
    lon = float(lon_raw) if lon_raw not in (None, "") else None

    osm_type_raw = row.get(args.osm_type_column)
    osm_id_raw = row.get(args.osm_id_column)
    osm_type = str(osm_type_raw) if osm_type_raw not in (None, "") else None
    osm_id = str(osm_id_raw) if osm_id_raw not in (None, "") else None

    tags = {k: v for k, v in row.items() if v not in (None, "")}
    level, level_reason = infer_level_with_reason(facility_type, tags)
    specialities = infer_specialities(facility_type, tags)
    capacity_max = LEVEL_CAPACITY[level]
    tags_with_reason = dict(tags)
    tags_with_reason["mapping_reason_level"] = level_reason

    return {
        "id": generate_id(name, osm_type, osm_id, lat, lon),
        "name": name,
        "lat": lat,
        "lon": lon,
        "osm_type": osm_type,
        "osm_id": osm_id,
        "level": level,
        "specialities": ",".join(specialities),
        "raw_tags_json": json.dumps(tags_with_reason, ensure_ascii=False),
        "capacity_max": capacity_max,
        "capacity_available": capacity_max,
        "estimated_wait_minutes": LEVEL_WAIT[level],
        "catchment_population": 0,
    }


def upsert_centres(centres: list[dict[str, Any]]) -> tuple[int, int]:
    inserted = 0
    updated = 0
    with get_session() as session:
        for centre in centres:
            existing = None
            if centre["osm_type"] and centre["osm_id"]:
                existing = session.scalar(
                    select(CentreModel).where(
                        CentreModel.osm_type == centre["osm_type"],
                        CentreModel.osm_id == centre["osm_id"],
                    )
                )
            if existing is None:
                existing = session.get(CentreModel, centre["id"])

            if existing is None:
                session.add(CentreModel(**centre))
                inserted += 1
            else:
                existing.name = centre["name"]
                existing.lat = centre["lat"]
                existing.lon = centre["lon"]
                existing.osm_type = centre["osm_type"]
                existing.osm_id = centre["osm_id"]
                existing.level = centre["level"]
                existing.specialities = centre["specialities"]
                existing.raw_tags_json = centre["raw_tags_json"]
                existing.capacity_max = centre["capacity_max"]
                existing.capacity_available = min(existing.capacity_available, centre["capacity_max"])
                if existing.capacity_available <= 0:
                    existing.capacity_available = centre["capacity_max"]
                existing.estimated_wait_minutes = centre["estimated_wait_minutes"]
                existing.catchment_population = centre["catchment_population"]
                updated += 1

        session.commit()

    return inserted, updated


def main() -> None:
    args = parse_args()
    init_db()

    path = Path(args.input)
    if not path.exists():
        raise FileNotFoundError(f"Input not found: {path}")

    rows = parse_geojson(path) if args.format == "geojson" else parse_csv(path)
    centres = [to_centre(row, args) for row in rows]
    inserted, updated = upsert_centres(centres)

    print(json.dumps({"read": len(rows), "inserted": inserted, "updated": updated}, indent=2))


if __name__ == "__main__":
    main()
