from __future__ import annotations

import argparse
from collections import Counter
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
    parser = argparse.ArgumentParser(description="Import health facilities from Geofabrik POI shapefile")
    parser.add_argument(
        "--input-shp",
        type=str,
        required=True,
        help="Path to gis_osm_pois_free_1.shp",
    )
    parser.add_argument(
        "--include-fclass",
        type=str,
        default="hospital,clinic,doctors,dentist,pharmacy",
        help="Comma-separated fclass filters",
    )
    parser.add_argument(
        "--exclude-empty-name",
        action="store_true",
        help="Skip records without a facility name",
    )
    parser.add_argument(
        "--quality-report",
        type=str,
        default=None,
        help="Optional output path for import quality report JSON",
    )
    return parser.parse_args()


def infer_level_from_fclass(fclass: str, name: str = "") -> str:
    return infer_level_with_reason(fclass=fclass, name=name)[0]


def infer_level_with_reason(*, fclass: str, name: str) -> tuple[str, str]:
    normalized = (fclass or "").strip().lower()
    name_l = (name or "").strip().lower()
    corpus = f"{normalized} {name_l}"

    primary_terms = [
        "dispensary",
        "health post",
        "healthpost",
        "outpost",
        "chemist",
    ]
    tertiary_terms = [
        "referral hospital",
        "county referral",
        "teaching hospital",
        "national hospital",
        "level 6",
        "level 5",
    ]
    secondary_terms = [
        "sub county hospital",
        "district hospital",
        "county hospital",
        "health centre",
        "health center",
        "medical centre",
        "medical center",
        "clinic",
        "hospital",
    ]

    if any(term in corpus for term in primary_terms):
        return "primary", "name_keyword_primary"
    if any(term in corpus for term in tertiary_terms):
        return "tertiary", "name_keyword_tertiary"
    if normalized in {"doctors", "dentist", "pharmacy"}:
        return "primary", "fclass_primary"
    if normalized == "clinic":
        return "secondary", "fclass_secondary"
    if normalized == "hospital":
        # Conservative default: many OSM 'hospital' entries are not true tertiary referral centres.
        return "secondary", "fclass_hospital_default_secondary"
    if any(term in corpus for term in secondary_terms):
        return "secondary", "name_keyword_secondary"
    return "primary", "fallback_primary"


def infer_specialities(*, fclass: str, name: str) -> list[str]:
    corpus = f"{fclass} {name}".lower()
    specialities: list[str] = []
    if any(tok in corpus for tok in ["matern", "obstet", "antenatal", "prenatal"]):
        specialities.append("maternal")
    if any(tok in corpus for tok in ["pediatric", "paediatric", "children", "child"]):
        specialities.append("pediatric")
    if not specialities:
        specialities.append("general")
    elif "general" not in specialities:
        specialities.append("general")
    return specialities


def generate_centre_id(*, osm_id: str | None, fclass: str, name: str, lat: float, lon: float) -> str:
    if osm_id:
        return f"GEO_node_{osm_id}"
    digest = hashlib.sha1(f"{fclass}|{name}|{lat}|{lon}".encode("utf-8")).hexdigest()[:16]
    return f"GEO_fallback_{digest}"


def _safe_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load_pois_from_shapefile(path: Path) -> list[dict[str, Any]]:
    try:
        import shapefile  # pyshp
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("Missing dependency 'pyshp'. Install requirements and retry.") from exc

    reader = shapefile.Reader(str(path))
    fields = [f[0] for f in reader.fields if f[0] != "DeletionFlag"]
    rows: list[dict[str, Any]] = []

    for shape_record in reader.iterShapeRecords():
        attrs = dict(zip(fields, shape_record.record))
        shape = shape_record.shape
        if not shape.points:
            continue

        lon = _safe_float(shape.points[0][0])
        lat = _safe_float(shape.points[0][1])
        if lat is None or lon is None:
            continue

        row = dict(attrs)
        row["lat"] = lat
        row["lon"] = lon
        rows.append(row)

    return rows


def to_centre(row: dict[str, Any]) -> dict[str, Any]:
    name = str(row.get("name") or "").strip()
    fclass = str(row.get("fclass") or "").strip().lower()
    osm_id = str(row.get("osm_id") or "").strip() or None

    lat = _safe_float(row.get("lat"))
    lon = _safe_float(row.get("lon"))
    if lat is None or lon is None:
        raise ValueError("Missing lat/lon for POI row")

    level, level_reason = infer_level_with_reason(fclass=fclass, name=name)
    capacity_max = LEVEL_CAPACITY[level]
    specialities = infer_specialities(fclass=fclass, name=name)
    raw_tags = {
        "source": "geofabrik_pois",
        "fclass": fclass,
        "name": name,
        "code": row.get("code"),
        "mapping_reason_level": level_reason,
    }

    return {
        "id": generate_centre_id(osm_id=osm_id, fclass=fclass, name=name, lat=lat, lon=lon),
        "name": name or f"{fclass}_{osm_id or 'unknown'}",
        "lat": lat,
        "lon": lon,
        "osm_type": "node",
        "osm_id": osm_id,
        "level": level,
        "specialities": ",".join(specialities),
        "raw_tags_json": json.dumps(raw_tags, ensure_ascii=False),
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


def build_quality_report(*, rows: list[dict[str, Any]], centres: list[dict[str, Any]], exclude_empty_name: bool) -> dict:
    level_counts = Counter(c["level"] for c in centres)
    speciality_counts: Counter[str] = Counter()
    for centre in centres:
        values = [item.strip() for item in centre["specialities"].split(",") if item.strip()]
        speciality_counts.update(values)

    fclass_counts = Counter(str(r.get("fclass") or "").strip().lower() for r in rows)
    empty_name_count = sum(1 for r in rows if not str(r.get("name") or "").strip())
    duplicate_osm = Counter(str(c["osm_id"]) for c in centres if c.get("osm_id"))
    duplicate_osm = {k: v for k, v in duplicate_osm.items() if v > 1}

    suspicious_rules = {
        "dispensary_not_primary": 0,
        "referral_not_tertiary": 0,
        "hospital_primary": 0,
    }
    for centre in centres:
        name_l = str(centre["name"]).lower()
        level = centre["level"]
        if "dispensary" in name_l and level != "primary":
            suspicious_rules["dispensary_not_primary"] += 1
        if "referral" in name_l and level != "tertiary":
            suspicious_rules["referral_not_tertiary"] += 1
        if "hospital" in name_l and level == "primary":
            suspicious_rules["hospital_primary"] += 1

    return {
        "rows_considered": len(rows),
        "centres_prepared": len(centres),
        "exclude_empty_name": exclude_empty_name,
        "empty_name_rows": empty_name_count,
        "level_counts": dict(level_counts),
        "speciality_counts": dict(speciality_counts),
        "fclass_counts": dict(fclass_counts),
        "duplicate_osm_id_count": len(duplicate_osm),
        "suspicious_mapping_flags": suspicious_rules,
    }


def main() -> None:
    args = parse_args()
    init_db()

    input_path = Path(args.input_shp)
    if not input_path.exists():
        raise FileNotFoundError(f"Shapefile not found: {input_path}")

    include_fclass = {item.strip().lower() for item in args.include_fclass.split(",") if item.strip()}
    rows = load_pois_from_shapefile(input_path)

    kept_rows: list[dict[str, Any]] = []
    for row in rows:
        fclass = str(row.get("fclass") or "").strip().lower()
        name = str(row.get("name") or "").strip()
        if include_fclass and fclass not in include_fclass:
            continue
        if args.exclude_empty_name and not name:
            continue
        kept_rows.append(row)

    centres = [to_centre(row) for row in kept_rows]
    inserted, updated = upsert_centres(centres)
    quality = build_quality_report(rows=kept_rows, centres=centres, exclude_empty_name=args.exclude_empty_name)

    if args.quality_report:
        quality_path = Path(args.quality_report)
        quality_path.parent.mkdir(parents=True, exist_ok=True)
        quality_path.write_text(json.dumps(quality, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "read": len(rows),
                "kept": len(kept_rows),
                "inserted": inserted,
                "updated": updated,
                "include_fclass": sorted(include_fclass),
                "quality_summary": {
                    "level_counts": quality["level_counts"],
                    "suspicious_mapping_flags": quality["suspicious_mapping_flags"],
                },
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
