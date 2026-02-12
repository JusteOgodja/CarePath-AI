from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import httpx
from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.models import CentreModel, ReferenceModel, get_session, init_db


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build referral edges from geo coordinates")
    parser.add_argument("--k-nearest", type=int, default=2, help="Max nearest targets per rule")
    parser.add_argument("--speed-kmh", type=float, default=40.0)
    parser.add_argument("--bidirectional", action="store_true", help="Create reverse edge for each generated edge")
    parser.add_argument("--osrm-server", type=str, default=None, help="Optional local OSRM base URL")
    parser.add_argument("--no-replace", action="store_true", help="Do not clear existing edges before insert")
    parser.add_argument("--no-alternatives", action="store_true", help="Disable optional alternative routes")
    return parser.parse_args()


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)

    a = (math.sin(d_lat / 2) ** 2) + math.cos(p1) * math.cos(p2) * (math.sin(d_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius * c


def estimate_travel_minutes(distance_km: float, speed_kmh: float) -> int:
    if speed_kmh <= 0:
        raise ValueError("speed_kmh must be > 0")
    return max(1, int(round((distance_km / speed_kmh) * 60.0)))


def estimate_travel_minutes_osrm(
    *,
    source: CentreModel,
    target: CentreModel,
    osrm_server: str | None,
    speed_kmh: float,
) -> int:
    if osrm_server and source.lat is not None and source.lon is not None and target.lat is not None and target.lon is not None:
        try:
            coords = f"{source.lon},{source.lat};{target.lon},{target.lat}"
            url = f"{osrm_server.rstrip('/')}/route/v1/driving/{coords}"
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(url, params={"overview": "false"})
                resp.raise_for_status()
                payload = resp.json()
            routes = payload.get("routes", [])
            if routes:
                duration_s = float(routes[0].get("duration", 0.0))
                if duration_s > 0:
                    return max(1, int(round(duration_s / 60.0)))
        except Exception:
            pass

    if source.lat is None or source.lon is None or target.lat is None or target.lon is None:
        return 1
    dist = haversine_km(source.lat, source.lon, target.lat, target.lon)
    return estimate_travel_minutes(dist, speed_kmh)


def nearest_targets(source: CentreModel, targets: list[CentreModel], k: int) -> list[tuple[CentreModel, float]]:
    pairs: list[tuple[CentreModel, float]] = []
    if source.lat is None or source.lon is None:
        return pairs

    for target in targets:
        if target.id == source.id:
            continue
        if target.lat is None or target.lon is None:
            continue
        dist = haversine_km(source.lat, source.lon, target.lat, target.lon)
        pairs.append((target, dist))

    pairs.sort(key=lambda x: x[1])
    return pairs[: max(k, 1)]


def build_edges(
    *,
    k_nearest: int,
    speed_kmh: float,
    replace: bool,
    with_alternatives: bool,
    bidirectional: bool,
    osrm_server: str | None,
) -> tuple[int, int]:
    init_db()

    created = 0
    skipped = 0
    with get_session() as session:
        centres = session.scalars(select(CentreModel)).all()
        by_level: dict[str, list[CentreModel]] = {"primary": [], "secondary": [], "tertiary": []}
        for centre in centres:
            by_level.setdefault(centre.level, []).append(centre)

        if replace:
            session.query(ReferenceModel).delete()

        existing = {
            (ref.source_id, ref.dest_id)
            for ref in session.scalars(select(ReferenceModel)).all()
        }

        def add_edge(source: CentreModel, target: CentreModel) -> None:
            nonlocal created, skipped
            key = (source.id, target.id)
            if key in existing:
                skipped += 1
                return
            travel = estimate_travel_minutes_osrm(
                source=source,
                target=target,
                osrm_server=osrm_server,
                speed_kmh=speed_kmh,
            )
            session.add(
                ReferenceModel(
                    source_id=source.id,
                    dest_id=target.id,
                    travel_minutes=travel,
                )
            )
            existing.add(key)
            created += 1

        def add_rule(sources: list[CentreModel], targets: list[CentreModel], fanout: int) -> None:
            nonlocal created, skipped
            for source in sources:
                near = nearest_targets(source, targets, fanout)
                for target, _dist in near:
                    add_edge(source, target)
                    if bidirectional:
                        add_edge(target, source)

        add_rule(by_level.get("primary", []), by_level.get("secondary", []), k_nearest)
        add_rule(by_level.get("secondary", []), by_level.get("tertiary", []), k_nearest)

        if with_alternatives:
            alt_k = max(1, min(k_nearest, 2))
            add_rule(by_level.get("primary", []), by_level.get("tertiary", []), alt_k)
            add_rule(by_level.get("secondary", []), by_level.get("secondary", []), 1)

        session.commit()

    return created, skipped


def main() -> None:
    args = parse_args()
    created, skipped = build_edges(
        k_nearest=args.k_nearest,
        speed_kmh=args.speed_kmh,
        replace=not args.no_replace,
        with_alternatives=not args.no_alternatives,
        bidirectional=args.bidirectional,
        osrm_server=args.osrm_server,
    )
    print({"created_edges": created, "skipped_edges": skipped})


if __name__ == "__main__":
    main()
