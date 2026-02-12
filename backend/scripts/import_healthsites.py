from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import get_healthsites_api_key, get_healthsites_base_url
from app.db.models import CentreModel, get_session, init_db
from app.integrations.healthsites_client import HealthsitesClient

SEVERITY_LEVEL_CAPACITY = {
    "primary": 10,
    "secondary": 30,
    "tertiary": 120,
}

SEVERITY_LEVEL_WAIT = {
    "primary": 15,
    "secondary": 30,
    "tertiary": 60,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import facilities from Healthsites API v3")
    parser.add_argument("--country", type=str, default=None)
    parser.add_argument("--extent", type=str, default=None, help="minLng,minLat,maxLng,maxLat")
    parser.add_argument("--from", dest="date_from", type=str, default=None)
    parser.add_argument("--to", dest="date_to", type=str, default=None)
    parser.add_argument("--output", type=str, default="json", choices=["json", "geojson"])
    parser.add_argument("--flat-properties", type=str, default="true", choices=["true", "false"])
    parser.add_argument("--tag-format", type=str, default="osm")
    parser.add_argument("--max-pages", type=int, default=None)
    return parser.parse_args()


def _extract_properties(item: dict[str, Any]) -> dict[str, Any]:
    if isinstance(item.get("properties"), dict):
        return dict(item["properties"])
    return dict(item)


def _extract_coords(item: dict[str, Any], props: dict[str, Any]) -> tuple[float | None, float | None]:
    if isinstance(item.get("geometry"), dict):
        coords = item["geometry"].get("coordinates")
        if isinstance(coords, list) and len(coords) >= 2:
            return float(coords[1]), float(coords[0])

    lat = props.get("lat") or props.get("latitude")
    lon = props.get("lon") or props.get("lng") or props.get("longitude")
    try:
        return (float(lat), float(lon))
    except (TypeError, ValueError):
        return (None, None)


def _collect_tags(props: dict[str, Any]) -> dict[str, Any]:
    tags = {}
    for key, value in props.items():
        if key in {"name", "lat", "lon", "latitude", "longitude", "lng"}:
            continue
        if value is None:
            continue
        tags[str(key)] = value
    return tags


def _infer_level(props: dict[str, Any], tags: dict[str, Any]) -> str:
    corpus = " ".join([str(v).lower() for v in [props.get("amenity"), props.get("healthcare"), props.get("facility_type"), *tags.values()] if v is not None])

    if any(token in corpus for token in ["tertiary", "referral_hospital", "teaching hospital", "hospital"]):
        return "tertiary"
    if any(token in corpus for token in ["health_center", "health centre", "clinic", "medical_center", "polyclinic"]):
        return "secondary"
    if any(token in corpus for token in ["dispensary", "health_post", "health post", "outpost"]):
        return "primary"
    return "primary"


def _infer_specialities(tags: dict[str, Any], props: dict[str, Any]) -> list[str]:
    corpus = " ".join([str(v).lower() for v in [props.get("healthcare:speciality"), props.get("speciality"), *tags.values()] if v is not None])

    specialities: list[str] = []
    if any(token in corpus for token in ["maternity", "maternal", "obstetric", "antenatal", "prenatal"]):
        specialities.append("maternal")
    if any(token in corpus for token in ["pediatric", "paediatric", "children", "child"]):
        specialities.append("pediatric")
    if not specialities:
        specialities.append("general")
    elif "general" not in specialities:
        specialities.append("general")
    return sorted(set(specialities), key=specialities.index)


def _extract_identity(props: dict[str, Any]) -> tuple[str | None, str | None]:
    osm_type = props.get("osm_type") or props.get("osm:type") or props.get("type")
    osm_id = props.get("osm_id") or props.get("osm:id") or props.get("id")

    if osm_type is not None:
        osm_type = str(osm_type)
    if osm_id is not None:
        osm_id = str(osm_id)
    return osm_type, osm_id


def _centre_id(name: str, osm_type: str | None, osm_id: str | None, lat: float | None, lon: float | None) -> str:
    if osm_type and osm_id:
        return f"HS_{osm_type}_{osm_id}"

    base = f"{name}|{lat}|{lon}"
    digest = hashlib.sha1(base.encode("utf-8")).hexdigest()[:16]
    return f"HS_FALLBACK_{digest}"


def facility_to_centre(item: dict[str, Any]) -> dict[str, Any] | None:
    props = _extract_properties(item)
    tags = _collect_tags(props)
    name = str(props.get("name") or props.get("facility_name") or "Unnamed facility").strip()
    lat, lon = _extract_coords(item, props)
    osm_type, osm_id = _extract_identity(props)

    level = _infer_level(props, tags)
    specialities = _infer_specialities(tags, props)
    capacity_max = SEVERITY_LEVEL_CAPACITY[level]
    estimated_wait = SEVERITY_LEVEL_WAIT[level]

    return {
        "id": _centre_id(name, osm_type, osm_id, lat, lon),
        "name": name,
        "lat": lat,
        "lon": lon,
        "osm_type": osm_type,
        "osm_id": osm_id,
        "level": level,
        "specialities": ",".join(specialities),
        "raw_tags_json": json.dumps(tags, ensure_ascii=False),
        "capacity_max": capacity_max,
        "capacity_available": capacity_max,
        "estimated_wait_minutes": estimated_wait,
        "catchment_population": 0,
    }


def upsert_centres(items: list[dict[str, Any]]) -> tuple[int, int]:
    inserted = 0
    updated = 0
    with get_session() as session:
        for centre in items:
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
                continue

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

    api_key = get_healthsites_api_key()
    base_url = get_healthsites_base_url()
    client = HealthsitesClient(base_url=base_url)

    mapped: list[dict[str, Any]] = []
    flat_props = args.flat_properties.lower() == "true"
    for item in client.iter_facilities(
        api_key=api_key,
        country=args.country,
        extent=args.extent,
        date_from=args.date_from,
        date_to=args.date_to,
        flat_properties=flat_props,
        tag_format=args.tag_format,
        output=args.output,
        max_pages=args.max_pages,
    ):
        converted = facility_to_centre(item)
        if converted is not None:
            mapped.append(converted)

    inserted, updated = upsert_centres(mapped)
    print(
        json.dumps(
            {
                "fetched": len(mapped),
                "inserted": inserted,
                "updated": updated,
                "country": args.country,
                "max_pages": args.max_pages,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
